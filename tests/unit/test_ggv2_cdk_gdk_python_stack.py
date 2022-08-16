import aws_cdk as core
import aws_cdk.assertions as assertions

from ggv2_cdk_gdk_python.ggv2_cdk_gdk_python_stack import Ggv2CdkGdkPythonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ggv2_cdk_gdk_python/ggv2_cdk_gdk_python_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Ggv2CdkGdkPythonStack(app, "ggv2-cdk-gdk-python")
    template = assertions.Template.from_stack(stack)

