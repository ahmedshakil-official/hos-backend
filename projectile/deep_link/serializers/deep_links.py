"""Serializer for our Deep Link App."""
import os

import requests

from urllib.parse import quote_plus

from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from deep_link.models import DeepLink


class DeepLinkMeta(ListSerializer.Meta):
    model = DeepLink
    fields = ListSerializer.Meta.fields + (
        "name",
        "description",
        "original_link",
        "short_link",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class DeepLinkModelSerializer:
    class List(ListSerializer):

        class Meta(DeepLinkMeta):
            fields = DeepLinkMeta.fields + (
                "long_dynamic_link",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
                "long_dynamic_link",
            )

    class Post(ListSerializer):
        fallback_link = serializers.URLField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )
        fallback_to_playstore = serializers.BooleanField(
            write_only=True,
            allow_null=True,
            required=False,
            default=False,
        )
        # Fields for UTM parameters
        utm_source = serializers.CharField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )
        utm_medium = serializers.CharField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )
        utm_campaign = serializers.CharField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )
        # Fields for social meta tag parameters
        social_title = serializers.CharField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )
        social_description = serializers.CharField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )
        social_image = serializers.CharField(
            write_only=True,
            allow_blank=True,
            allow_null=True,
            required=False,
        )


        class Meta(DeepLinkMeta):
            fields = DeepLinkMeta.fields + (
                "long_dynamic_link",
                "fallback_link",
                "fallback_to_playstore",
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "social_title",
                "social_description",
                "social_image",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
                "short_link",
                "long_dynamic_link",
            )

        def create(self, validated_data):
            original_link = validated_data.get("original_link", None)
            fallback_link = validated_data.get("fallback_link", None)
            fallback_to_playstore = validated_data.get("fallback_to_playstore", False)

            if fallback_link is None or fallback_link == "":
                fallback_link = original_link

            api_key = os.environ.get("DYNAMIC_LINK_API_KEY", None)
            domain_uri_prefix = os.environ.get("DOMAIN_URI_PREFIX", "https://healthosdev.page.link")
            android_apn = os.environ.get("ANDROID_APN" , "com.healthosbd.ecomretail")

            # Construct the base long dynamic link
            long_dynamic_link = f"{domain_uri_prefix}/?link={original_link}&apn={android_apn}"

            api_url = "https://firebasedynamiclinks.googleapis.com/v1/shortLinks?key={}".format(api_key)

            if not api_key:
                raise serializers.ValidationError("Api key is missing! Api key is required to create a dynamic link!")

            # Include the UTM parameters in the original link
            utm_source = validated_data.pop("utm_source", "")
            utm_medium = validated_data.pop("utm_medium", "")
            utm_campaign = validated_data.pop("utm_campaign", "")

            if utm_source:
                long_dynamic_link += f"&utm_source={quote_plus(utm_source)}"
            if utm_medium:
                long_dynamic_link += f"&utm_medium={quote_plus(utm_medium)}"
            if utm_campaign:
                long_dynamic_link += f"&utm_campaign={quote_plus(utm_campaign)}"

            # Include social meta tag parameters from validated_data
            social_title = validated_data.pop("social_title", "")
            social_description = validated_data.pop("social_description", "")
            social_image = validated_data.pop("social_image", "")

            if social_title:
                long_dynamic_link += f"&st={quote_plus(social_title)}"
            if social_description:
                long_dynamic_link += f"&sd={quote_plus(social_description)}"
            if social_image:
                long_dynamic_link += f"&si={social_image}"
            payload = {
                "dynamicLinkInfo": {
                    "domainUriPrefix": domain_uri_prefix,
                    "link": original_link,
                    "androidInfo": {
                        "androidPackageName": android_apn,
                    },
                    "analyticsInfo": {
                        "googlePlayAnalytics": {
                            "utmCampaign": utm_campaign,
                            "utmMedium": utm_medium,
                            "utmSource": utm_source,
                        }
                    },
                    "socialMetaTagInfo": {
                        "socialTitle": social_title,
                        "socialDescription": social_description,
                        "socialImageLink": social_image,
                    }
                }
            }

            if not fallback_to_playstore:
                payload["dynamicLinkInfo"]["androidInfo"]["androidFallbackLink"] = fallback_link
                long_dynamic_link += f"&afl={fallback_link}"

            try:
                # If deep link already exists then return the previous link
                deep_link = DeepLink.objects.get(long_dynamic_link=long_dynamic_link)
            except DeepLink.DoesNotExist:
                response = requests.post(api_url, json=payload, timeout=10)
                data = response.json()
                # if dynamic link couldn't created then raise error
                try:
                    short_link = data["shortLink"]
                except KeyError:
                    raise serializers.ValidationError("Couldn't get Dynamic url from firebase")

                # Create a dynamic link object
                deep_link = DeepLink.objects.create(
                    name = validated_data.get("name", ""),
                    description = validated_data.get("description", ""),
                    long_dynamic_link = long_dynamic_link,
                    original_link=original_link,
                    short_link=short_link,
                    entry_by_id=self.context.get("request").user.id
                )

            return deep_link
