from api.models.models import Feature


class FeatureNotFoundException(RuntimeError):
    def __init__(self, feature: Feature):
        self.feature = feature

    def __repr__(self):
        return f"Feature not found: {self.feature.name}"
