from krita import Krita, Extension  # type: ignore
from .agent_docker import StoryEditorAgentFactory


class StoryEditorAgentExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.agent_docker_factory = None

    def setup(self):
        self.agent_docker_factory = StoryEditorAgentFactory()
        Krita.instance().addDockWidgetFactory(self.agent_docker_factory)

    def createActions(self, window):
        """Called after Krita window is initialized"""
        # This method can be used for additional initialization if needed
        pass


# Register all extensions with Krita
Krita.instance().addExtension(StoryEditorAgentExtension(Krita.instance()))
