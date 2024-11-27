import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer

# Initialize glfw
if not glfw.init():
    raise Exception("glfw can not be initialized!")

# Create a window
window = glfw.create_window(1280, 720, "OpenGL Context", None, None)
if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")

# Make the OpenGL context current
glfw.make_context_current(window)

# Initialize ImGui
imgui.create_context()
impl = GlfwRenderer(window)

# Main loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    impl.process_inputs()
    imgui.new_frame()

    with imgui.begin("Hello"):
        imgui.text("Text")

    # Rendering
    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)

# Cleanup
impl.shutdown()
imgui.destroy_context()
glfw.terminate()
