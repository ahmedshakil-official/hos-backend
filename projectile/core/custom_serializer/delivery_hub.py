"""Serializer for Delivery Hub."""
from itertools import chain

from rest_framework import serializers

from common.custom_serializer.cu_base_organization_wise_serializer import ListSerializer

from core.enums import DhakaThana
from core.models import DeliveryHub, Organization, Person

from ..utils import user_detail_cache_expires_by_organization_delivery_thana


def check_duplicate_area_in_delivery_hubs(delivery_hubs, hub_areas):
    """This method check weather the area is already added in any hubs or not."""
    areas = list(chain(*delivery_hubs))
    for area in hub_areas:
        if area in areas:
            return True
    return False


def validate_hub_areas(hub_areas):
        """This function check provided area is valid or not."""
        valid_hub_areas = DhakaThana.get_values()
        invalid_areas = [area for area in hub_areas if area not in valid_hub_areas]
        if invalid_areas:
            raise serializers.ValidationError({"detail": "Invalid areas in hub_areas: {}".format(invalid_areas)})


class DeliveryHubMeta(ListSerializer.Meta):
    model = DeliveryHub
    fields = ListSerializer.Meta.fields + (
        "name",
        "description",
        "address",
        "hub_areas",
    )
    read_only_fields = ListSerializer.Meta.read_only_fields + (
    )


class DeliveryHubModelSerializer:
    class List(ListSerializer):
        class Meta(DeliveryHubMeta):
            fields = DeliveryHubMeta.fields + (
                "short_code",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
            )

        def validate(self, attrs):
            # Validation for delivery hub create with empty areas
            hub_areas = attrs.get("hub_areas", [])

            if not hub_areas:
                raise serializers.ValidationError({"detail": "You need at least one area for a delivery hub"})

            # Check for invalid Hub Areas
            validate_hub_areas(hub_areas=hub_areas)

            # Validation for hub areas
            delivery_hubs = DeliveryHub().get_all_actives().values_list("hub_areas", flat=True)

            # Check if the area is already added in any hub or not
            if check_duplicate_area_in_delivery_hubs(delivery_hubs=delivery_hubs, hub_areas=hub_areas):
                raise serializers.ValidationError({"detail": "Delivery Hub with this area already exits."})

            return super().validate(attrs)

        def create(self, validated_data):
            instance = super().create(validated_data)

            Organization().get_all_actives().filter(
                    delivery_thana__in=instance.hub_areas,
                ).exclude(delivery_hub=instance).update(
                    delivery_hub=instance,
                )

            person = Person().get_all_actives().filter(
                    organization__delivery_thana__in=instance.hub_areas
                ).exclude(delivery_hub_id=instance.id).update(
                    delivery_hub=instance,
                )
            user_detail_cache_expires_by_organization_delivery_thana(instance.hub_areas)

            return instance

    class Detail(ListSerializer):
        class Meta(DeliveryHubMeta):
            fields = DeliveryHubMeta.fields + (
                "short_code",
            )
            read_only_fields = ListSerializer.Meta.read_only_fields + (
            )

        def update(self, instance, validated_data):
            old_areas = instance.hub_areas
            # If there are delivery hubs with overlapping areas, raise a validation error
            updated_areas = validated_data.get("hub_areas", None)
            # If updated areas is an empty list raise validation error.
            if updated_areas == []:
                raise serializers.ValidationError({"detail": "At least one area is required for a delivery hub"})

            if updated_areas:
                # Check for valid delivery hub area
                validate_hub_areas(hub_areas=updated_areas)

                delivery_hubs = DeliveryHub().get_all_actives().exclude(
                    id=instance.id
                ).values_list("hub_areas", flat=True)

                # Check if the area is already added in any hub or not
                if check_duplicate_area_in_delivery_hubs(delivery_hubs=delivery_hubs, hub_areas=updated_areas):
                    raise serializers.ValidationError({"detail": "Delivery Hub with this area already exits."})

            instance = super().update(instance, validated_data)

            for area in old_areas:
                if area not in instance.hub_areas:
                    organizations = Organization().get_all_actives().filter(delivery_thana=area)
                    person = Person().get_all_actives().filter(organization__delivery_thana=area)

                    if organizations:
                        organizations.update(delivery_hub=None)

                    if person:
                        person.update(delivery_hub=None)
                    # clear cache for old areas
                    user_detail_cache_expires_by_organization_delivery_thana(old_areas)

            for area in instance.hub_areas:
                organizations = (Organization().get_all_actives().filter(delivery_thana=area)
                                 .exclude(delivery_hub=instance))

                person = (Person().get_all_actives().filter(organization__delivery_thana=area)
                                 .exclude(delivery_hub=instance))

                if organizations:
                    organizations.update(delivery_hub=instance)

                if person:
                    person.update(delivery_hub=instance)

            # expire cache every update request
            user_detail_cache_expires_by_organization_delivery_thana(instance.hub_areas)
            return instance


class DeliveryHubNameCodeLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryHub
        fields = (
            "id",
            "alias",
            "name",
            "short_code",
        )