# PUBLIC 17 Semantic Hotfix Caveats and Rejected Alternatives

The hotfix removes or demotes `content_preference_signal` from representative rules because it is too broad. A marker present for most rows cannot separate a specific segment. It remains useful as a broad content-context cue for profile or action personalization.

`genre_preference_clear` remains usable because it is narrower and more interpretable as a genre concentration signal.

The large `other_needs_review` bucket is not forcibly split. This is deliberate. A cleaner-looking segmentation would be less trustworthy if it created groups without sufficient behavior evidence.

Age and gender are not representative rules. They remain profile audit and personalization variables only.

GB top20 remains the representative risk criterion because top10 is too narrow and top30 is too broad for the current provisional design. It is not a final campaign threshold.

Final campaign threshold selection is rejected because 17 is segmentation design. 07~10 pending validation is preserved because this hotfix does not complete or replace those stages.
