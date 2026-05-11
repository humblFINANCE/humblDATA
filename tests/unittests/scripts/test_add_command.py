import ast
import importlib.util
from pathlib import Path

ADD_COMMAND_PATH = Path(__file__).parents[3] / "scripts" / "add_command.py"
SPEC = importlib.util.spec_from_file_location("add_command", ADD_COMMAND_PATH)
assert SPEC is not None
add_command = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(add_command)
generate_category_controller = add_command.generate_category_controller


def write_existing_controller(project_root):
    controller_path = (
        project_root
        / "src"
        / "humbldata"
        / "toolbox"
        / "technical"
        / "technical_controller.py"
    )
    controller_path.parent.mkdir(parents=True)
    controller_path.write_text(
        '''"""Context: Toolbox || **Category: Technical**."""
from humbldata.core.standard_models.abstract.errors import HumblDataError
from humbldata.core.standard_models.toolbox import ToolboxQueryParams
from humbldata.core.utils.logger import setup_logger

logger = setup_logger(__name__)


class Technical:
    """
    Module for all technical analysis.

    Methods
    -------
    old_command(**kwargs: OldCommandQueryParams)
        Execute the OldCommand command.
    """

    def __init__(self, context_params: ToolboxQueryParams):
        self.context_params = context_params

    def old_command(self, **kwargs):
        return kwargs
'''
    )
    return controller_path


def test_generate_category_controller_adds_command_without_replacing_existing(
    tmp_path,
):
    controller_path = write_existing_controller(tmp_path)

    generate_category_controller(
        tmp_path,
        "toolbox",
        "technical",
        "new_command",
    )

    content = controller_path.read_text()
    tree = ast.parse(content)
    class_node = next(
        node for node in tree.body if isinstance(node, ast.ClassDef)
    )
    class_doc = ast.get_docstring(class_node)
    method_names = [
        node.name for node in class_node.body if isinstance(node, ast.FunctionDef)
    ]

    assert method_names == ["__init__", "old_command", "new_command"]
    assert content.count("def old_command") == 1
    assert content.count("def new_command") == 1
    assert "old_command(**kwargs: OldCommandQueryParams)" in class_doc
    assert "new_command(**kwargs: NewCommandQueryParams)" in class_doc


def test_generate_category_controller_is_idempotent(tmp_path):
    controller_path = write_existing_controller(tmp_path)

    for _ in range(2):
        generate_category_controller(
            tmp_path,
            "toolbox",
            "technical",
            "new_command",
        )

    content = controller_path.read_text()

    assert content.count("NewCommandQueryParams") == 4
    assert content.count("def new_command") == 1
    ast.parse(content)
