from __future__ import unicode_literals, absolute_import
import logging
import os
from tqdm import tqdm
from yaspin import yaspin
from django.core.cache import cache
from django.conf import settings
from django import VERSION as DJANGO_VERSION
from django.core.management.base import BaseCommand, CommandError
from six.moves import input
from django_elasticsearch_dsl.registries import registry

from core.models import Organization

ES_DB_NAME = os.environ.get('ES_REBUILD_DB_NAME', 'default')


class DisableLogger():
    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, _a, _b, _c):
        logging.disable(logging.NOTSET)


class Command(BaseCommand):
    help = 'Manage elasticsearch index.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            metavar='app[.model]',
            type=str,
            nargs='*',
            help="Specify the model or app to be updated in elasticsearch"
        )
        parser.add_argument(
            '--create',
            action='store_const',
            dest='action',
            const='create',
            help="Create the indices in elasticsearch"
        )
        parser.add_argument(
            '--populate',
            action='store_const',
            dest='action',
            const='populate',
            help="Populate elasticsearch indices with models data"
        )
        parser.add_argument(
            '--delete',
            action='store_const',
            dest='action',
            const='delete',
            help="Delete the indices in elasticsearch"
        )
        parser.add_argument(
            '--rebuild',
            action='store_const',
            dest='action',
            const='rebuild',
            help="Delete the indices and then recreate and populate them"
        )
        parser.add_argument(
            '-f',
            action='store_true',
            dest='force',
            help="Force operations without asking"
        )
        parser.add_argument(
            '--parallel',
            action='store_true',
            dest='parallel',
            help='Run populate/rebuild update multi threaded'
        )

        parser.add_argument(
            '--use_cache',
            action='store_true',
            dest='use_cache',
            default=False,
            help='Skip organization depending on cache'
        )

        parser.add_argument(
            '--cache_record_flush',
            action='store_true',
            default=True,
            dest='cache_record_flush',
            help='Flush Previous Cache'
        )

        parser.add_argument(
            '--no-parallel',
            action='store_false',
            dest='parallel',
            help='Run populate/rebuild update single threaded'
        )
        parser.set_defaults(parallel=getattr(settings, 'ELASTICSEARCH_DSL_PARALLEL', False))
        parser.add_argument(
            '--no-count',
            action='store_false',
            default=True,
            dest='count',
            help='Do not include a total count in the summary log line'
        )
        parser.add_argument(
            '--single',
            action='store_true',
            dest='single',
            help='Rebuild / Populate index one by one'
        )
        parser.add_argument('--custom_list', help="Model list", nargs='+')

    @staticmethod
    def _get_indexing_queryset(self, filters=None):
        """
        Build queryset (iterator) for use by indexing.
        """

        if filters is None:
            filters = {}
        qs = self.get_queryset().filter(**filters).using(ES_DB_NAME)

        kwargs = {}
        if DJANGO_VERSION >= (2,) and self.django.queryset_pagination:
            kwargs = {'chunk_size': self.django.queryset_pagination}
        iterator = qs.iterator(**kwargs)

        return iterator

    def _get_models(self, args):
        """
        Get Models from registry that match the --models args
        """
        if args:
            models = []
            for arg in args:
                arg = arg.lower()
                match_found = False

                for model in registry.get_models():
                    if model._meta.app_label == arg:
                        models.append(model)
                        match_found = True
                    elif '{}.{}'.format(
                        model._meta.app_label.lower(),
                        model._meta.model_name.lower()
                    ) == arg:
                        models.append(model)
                        match_found = True

                if not match_found:
                    raise CommandError("No model or app named {}".format(arg))
        else:
            models = registry.get_models()

        return set(models)

    def _create(self, models, options):
        for index in registry.get_indices(models):
            self.stdout.write("Creating index '{}'".format(index._name))
            index.create()

    def _populate(self, models, options):

        parallel = options['parallel']
        use_cache = options['use_cache']
        cache_record_flush = options['cache_record_flush']
        cache_key_prefix = getattr(
            settings, 'ELASTICSEARCH_DSL_PARALLEL_CACHE_PREFIX', 'elastic_search_record')

        if cache_record_flush and use_cache is False:
            cache.delete(cache_key_prefix)


        documents = registry.get_documents(models)
        # sort the documents as app order
        if not options['single']:
            documents = sorted(
                documents,
                key=lambda item: (item.Django.model._meta.app_label, item.Django.model._meta.model_name)
            )
        for doc in documents:
            model_name = doc.django.model.__name__
            self.stdout.write("Indexing {} '{}' objects {} of {} app".format(
                doc().get_queryset().using(ES_DB_NAME).count() if options['count'] else "all",
                model_name,
                "(parallel)" if parallel else "",
                doc.Django.model._meta.app_label)
            )
            _doc = doc()

            if False:
                pass

            else:
                organizations = Organization().get_all_organizations()
                organizations_count = organizations.count()
                organization_index = 1
                for organization in organizations:

                    skip_reindex = False

                    if use_cache:
                        current_state = cache.get(cache_key_prefix, {})
                        key = "{}_{}".format(doc.Index.name,organization.id)
                        if current_state is not None and key in current_state.keys():
                            if current_state[key] is True:
                                skip_reindex = True

                    if skip_reindex is False and use_cache is True:
                        current_state.update({"{}_{}".format(doc.Index.name,organization.id) : False })
                        cache.set(cache_key_prefix, current_state)


                    if skip_reindex is False:
                        message = "{} object, {} out of {} organization being indexed : {}".format(
                                model_name, organization_index, organizations_count, organization.name)
                        with yaspin(text=message, color="green") as spinner:
                            _doc._get_indexing_queryset = self._get_indexing_queryset
                            qs = _doc._get_indexing_queryset(_doc, {'organization__id' : organization.id})
                            _doc.update(qs, parallel=parallel)
                            organization_index = organization_index + 1
                            spinner.ok("✅ ")

                    if use_cache:
                        current_state = cache.get(cache_key_prefix, {})
                        current_state.update({"{}_{}".format(doc.Index.name,organization.id) : True })
                        cache.set(cache_key_prefix, current_state)

                skip_non_organization_reindex = False

                if use_cache:
                    current_state = cache.get(cache_key_prefix)
                    key = "{}_{}".format(doc.Index.name,'all')
                    if current_state is not None and key in current_state.keys():
                        if current_state[key] is True:
                            skip_non_organization_reindex = True

                if skip_non_organization_reindex is False and use_cache is True:
                    current_state.update({"{}_{}".format(doc.Index.name, 'all') : False })
                    cache.set(cache_key_prefix, current_state)


                if not skip_non_organization_reindex:

                    message = "{} object, non orgazinational data is being indexed".format(model_name)
                    with yaspin(text=message, color="green") as spinner:
                        _doc._get_indexing_queryset = self._get_indexing_queryset
                        qs = _doc._get_indexing_queryset(_doc, {'organization__isnull' : True})
                        _doc.update(qs, parallel=parallel)
                        spinner.ok("✅ ")

                if use_cache:
                    current_state = cache.get(cache_key_prefix)
                    if current_state is None:
                        current_state = {}
                    current_state.update({"{}_{}".format(doc.Index.name,'all') : True })
                    cache.set(cache_key_prefix, current_state,60*60)


    def _delete(self, models, options):
        index_names = [index._name for index in registry.get_indices(models)]

        if not options['force']:
            response = input(
                "Are you sure you want to delete "
                "the '{}' indexes? [n/Y]: ".format(", ".join(index_names)))
            if response.lower() != 'y':
                self.stdout.write('Aborted')
                return False

        for index in registry.get_indices(models):
            self.stdout.write("Deleting index '{}'".format(index._name))
            index.delete(ignore=404)
        return True

    def _rebuild(self, models, options):
        if not self._delete(models, options):
            return

        self._create(models, options)
        self._populate(models, options)

    def perform_action(self, models, action, options):
        self.stdout.write("ElasticSearch is using '{}' database".format(ES_DB_NAME))
        if action == 'create':
            self._create(models, options)
        elif action == 'populate':
            self._populate(models, options)
        elif action == 'delete':
            self._delete(models, options)
        elif action == 'rebuild':
            self._rebuild(models, options)
        else:
            raise CommandError(
                "Invalid action. Must be one of"
                " '--create','--populate', '--delete' or '--rebuild' ."
            )

    def handle(self, *args, **options):
        with DisableLogger():
            if not options['action']:
                raise CommandError(
                    "No action specified. Must be one of"
                    " '--create','--populate', '--delete' or '--rebuild' ."
                )

            action = options['action']
            rebuild_one_by_one = options['single']
            model_list = options['custom_list']
            if rebuild_one_by_one and options['models'] is None:
                for item in model_list:
                    model = self._get_models([item])
                    self.perform_action(model, action, options)
            else:
                models = self._get_models(options['models'])
                self.perform_action(models, action, options)
