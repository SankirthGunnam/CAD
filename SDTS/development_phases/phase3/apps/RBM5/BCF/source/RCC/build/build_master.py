from typing import Dict, Any, Optional, Callable
from pathlib import Path
import jinja2
import datetime
import os

from PySide6.QtCore import QObject, Signal

class BuildMaster(QObject):
    """Master class for handling code generation and build process"""

    # Single signal for all build events
    # Emitted for all build events with type and data
    build_event = Signal(dict)

    def __init__(self, rdb_manager=None, callback=None, event_handler=None):
        super().__init__()
        self.rdb_manager = rdb_manager
        self.callback = callback
        self.event_handler = event_handler
        self.template_dir = Path(__file__).parent / "code_generator"
        self.output_dir = None
        self.setup_jinja()

    def setup_jinja(self):
        """Setup Jinja2 environment with required extensions and settings"""
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            extensions=["jinja2.ext.i18n", "jinja2.ext.do", "jinja2.ext.loopcontrols"],
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add common filters and globals
        self.jinja_env.globals.update(
            {
                "now": datetime.datetime.now,
                "version": self.get_tool_version(),
                "project_code": self.get_project_code(),
            }
        )

    def get_tool_version(self) -> str:
        """Get the current tool version"""
        return "1.0.0"  # This should be replaced with actual version management

    def get_project_code(self) -> str:
        """Get the project code"""
        return "RCC"  # This should be replaced with actual project code

    def set_output_directory(self, output_dir: str):
        """Set the output directory for generated files"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _emit_event(self, event: dict):
        if self.event_handler:
            self.event_handler(event)
        else:
            self.build_event.emit(event)

    def generate_files(self, data: Dict[str, Any],
                       output_dir: Optional[str] = None):
        """Generate source and header files from templates"""
        try:
            if output_dir:
                self.set_output_directory(output_dir)

            if not self.output_dir:
                raise ValueError("Output directory not set")

            self._emit_event({"type": "build_started",
                              "message": "Starting code generation..."})

            # Common template data
            template_data = {
                "data": data,
                "build_time": datetime.datetime.now().strftime("%H:%M:%S"),
                "build_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "tool_version": self.get_tool_version(),
                "project_code": self.get_project_code(),
            }

            # Process all templates in the code_generator directory
            for template_file in self.template_dir.glob("*.jinja"):
                try:
                    template = self.jinja_env.get_template(template_file.name)
                    output_content = template.render(**template_data)

                    # Determine output file name and extension
                    output_name = template_file.stem
                    extension = ".h" if "header" in output_name else ".c"
                    output_file = self.output_dir / f"{output_name}{extension}"

                    # Write the generated content
                    with open(output_file, "w") as f:
                        f.write(output_content)

                    self._emit_event(
                        {"type": "file_generated", "file_path": str(output_file)}
                    )

                except Exception as e:
                    self._emit_event(
                        {
                            "type": "build_warning",
                            "message": f"Warning processing {
                                template_file.name}: {
                                str(e)}",
                        })
                    continue

            self._emit_event(
                {
                    "type": "build_completed",
                    "message": "Code generation completed successfully",
                }
            )
            if self.callback:
                self.callback()
        except ValueError as e:
            raise ValueError(e)
        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            self._emit_event(
                {"type": "build_failed", "message": error_msg, "details": str(e)}
            )
            if self.callback:
                self.callback()

    def get_build_status(self) -> Dict[str, Any]:
        """Get the current build status"""
        return {
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "tool_version": self.get_tool_version(),
            "project_code": self.get_project_code(),
        }
