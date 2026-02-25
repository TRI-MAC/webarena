import aws_cdk as cdk
import constructs
import jsii

@jsii.implements(cdk.IAspect)
class TagChecker:

    # Here we have all the required tags
    required_tags = set(["app-name", "environment","tri.owner","tri.project", "tri.owner.email"])

    def visit(self, node : constructs.IConstruct):
        tag_manager = cdk.TagManager.of(node)
        if tag_manager:
            node_tags = set(tag_manager.tag_values().keys())
            if not self.required_tags.issubset(node_tags):
                delta = list(self.required_tags - node_tags)
                cdk.Annotations.of(node).add_error("Missing Tags: " + ", ".join(delta) + " - Please ensure they appear in the configuration files")