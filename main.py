import imgui
import glfw
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
import os
from utils import glfw_utils
import importlib
import app


def main():
    # Variables
    background_color = (0, 0, 0, 1)
    time_buffer = "HH:mm"
    hours_to_run = 3
    is_enabled = False
    # Create window
    window = glfw_utils.impl_glfw_init_opengl()
    # OpenGL
    gl.glClearColor(*background_color)
    # Imgui
    imgui.create_context()
    impl = GlfwRenderer(window)

    # Hot reload app variables
    APP_MODULE_PATH = "app.py"
    app_module_last_mod_time = os.path.getmtime(APP_MODULE_PATH)

    while not glfw.window_should_close(window):
        # Hot reload app
        app_module_current_mod_time = os.path.getmtime(APP_MODULE_PATH)
        if app_module_current_mod_time != app_module_last_mod_time:
            # Reload the module if it has changed
            print("Reloading UI module...")
            try:
                importlib.reload(app)
            except ImportError:
                print("An error occured whiles importing module")
            app_module_last_mod_time = app_module_current_mod_time

        # Begin frame
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        app.render(window, time_buffer, hours_to_run, is_enabled)

        # End frame
        imgui.render()
        gl.glClearColor(*background_color)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
