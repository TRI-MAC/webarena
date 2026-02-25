import aws_cdk as cdk
from .TagChecker import TagChecker

class TRIChecker:
    def __init__(self, construct) -> None:
        cdk.Aspects.of(construct).add(TagChecker())
