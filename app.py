from typing import Optional
import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer


class App:
    def __init__(self, width=1280, height=720, title="ImGui + GLFW Window"):
        self.width = width
        self.height = height
        self.title = title
        self.window = None
        self.impl: Optional[GlfwRenderer] = None

    def __enter__(self):
        # Initialize GLFW
        if not glfw.init():
            raise Exception("GLFW can't be initialized")

        # Create GLFW window
        self.window = glfw.create_window(
            self.width, self.height, self.title, None, None
        )
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window can't be created")

        glfw.make_context_current(self.window)

        # Initialize ImGui
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        return self  # Return the instance for use within the `with` block

    def render(self, state):
        # Ensure self.impl is initialized
        if not self.impl:
            raise Exception("Renderer not initialized")

        # Poll for events and process ImGui inputs
        glfw.poll_events()
        self.impl.process_inputs()

        imgui.new_frame()

        # GUI code where `state` can influence the rendered elements
        imgui.begin("Example Window")
        imgui.text("Adjusting State Example")
        state["counter"] += 1
        imgui.text(f"Counter: {state['counter']}")
        imgui.end()

        # Rendering
        imgui.render()
        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)

        # Return updated state
        return state

    def __exit__(self, exc_type, exc_value, traceback):
        # Cleanup
        if self.impl:
            self.impl.shutdown()
        # Cleanup
        glfw.terminate()


def render_run_buttons(
    enabled,
    delayed_start_thread: StoppableThread | None,
    run_now_thread: StoppableThread | None,
):
    if enabled:
        imgui.push_item_flag(imgui.ITEM_DISABLED, True)
        imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha * 0.5)

    if imgui.button(
        "Delayed Start",
    ):
        print("Delayed start button clicked")
    imgui.same_line()
    # Run now button
    if imgui.button("Run now"):
        print("Run now button clicked")
    imgui.same_line()

    if enabled:
        imgui.pop_item_flag()
        imgui.pop_style_var()
    # Stop button
    if enabled and imgui.button("Stop"):
        thread.stop()

    return enabled


def render(window, time_buffer, hours_to_run, is_enabled, day_rules=[], date_rules=[]):
    # Get current GLFW window size and set ImGui window size to match it
    width, height = glfw.get_window_size(window)
    imgui.set_next_window_size(width, height)
    imgui.set_next_window_position(0, 0)

    # Set ImGui window flags to hide title bar, make it unmovable, and non-resizable
    window_flags = (
        imgui.WINDOW_NO_TITLE_BAR
        | imgui.WINDOW_NO_MOVE
        | imgui.WINDOW_NO_RESIZE
        | imgui.WINDOW_NO_COLLAPSE
    )

    # Fullscreen ImGui window
    with imgui.begin("Fullscreen ImGui Window", flags=window_flags):
        # Settings: Time to Start and Hours to Run
        imgui.text("Time to Start:")
        _, time_buffer = imgui.input_text("##time_start", time_buffer, 10)

        imgui.text("Hours to Run:")
        _, hours_to_run = imgui.input_int("##hours_to_run", hours_to_run)

        # Delayed Start Button - only enabled with a valid time
        valid_time = False
        try:
            datetime.strptime(time_buffer, "%H:%M")
            valid_time = True
        except ValueError:
            pass

        if is_enabled:
            imgui.push_item_flag(imgui.ITEM_DISABLED, True)
            imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha * 0.5)
        if imgui.button(
            "Delayed Start",
        ):
            print("Delayed start button clicked")
        imgui.same_line()
        # Run now button
        if imgui.button("Run now"):
            print("Run now button clicked")
        imgui.same_line()
        if is_enabled:
            imgui.pop_item_flag()
            imgui.pop_style_var()
        # Stop button
        if is_enabled and imgui.button("Stop"):
            pass

        imgui.separator()

        # Rules
        for i, rule in enumerate(date_rules):
            imgui.text(f"Date Rule {i+1}:")
            _, rule["date"] = imgui.input_text(f"##date_{i}", rule["date"], 10)
            imgui.same_line()
            _, rule["start_time"] = imgui.input_text(
                f"##start_time_{i}", rule["start_time"], 10
            )
            imgui.same_line()
            _, rule["end_time"] = imgui.input_text(
                f"##end_time_{i}", rule["end_time"], 10
            )
            if imgui.button(f"Delete Rule##delete_date_{i}"):
                date_rules.remove(rule)

        for i, rule in enumerate(day_rules):
            imgui.text(f"Day Rule {i+1}:")
            _, rule["day"] = imgui.input_text(f"##day_{i}", rule["day"], 10)
            imgui.same_line()
            _, rule["start_time"] = imgui.input_text(
                f"##start_time_{i}", rule["start_time"], 10
            )
            imgui.same_line()
            _, rule["end_time"] = imgui.input_text(
                f"##end_time_{i}", rule["end_time"], 10
            )
            if imgui.button(f"Delete Rule##delete_day_{i}"):
                day_rules.remove(rule)

        imgui.separator()

        # Add rules buttons
        if imgui.button("Add Date Rule"):
            pass
        imgui.same_line()
        if imgui.button("Add Day Rule"):
            pass

    return is_enabled
