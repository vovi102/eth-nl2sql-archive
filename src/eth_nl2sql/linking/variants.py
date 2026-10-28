"""Fixed interventions for the five-shot, non-fine-tuned linking comparison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkingVariant:
    multi_address: bool = True
    aliases: bool = True
    classes: bool = True
    properties: bool = True
    approximate: bool = True


VARIANTS = {
    "full": LinkingVariant(),
    "baseline": LinkingVariant(
        multi_address=False, classes=False, properties=False, approximate=False
    ),
    "no_multi_address": LinkingVariant(multi_address=False),
    "no_alias": LinkingVariant(aliases=False),
    "no_class": LinkingVariant(classes=False),
    "no_property": LinkingVariant(properties=False),
}

# All use the same B2 generator, complete schema and five retrieved examples.
EXPERIMENTS = {
    "b2l": "full",
    "b2l-baseline": "baseline",
    "b2l-no-multi-address": "no_multi_address",
    "b2l-no-alias": "no_alias",
    "b2l-no-class": "no_class",
    "b2l-no-property": "no_property",
}
