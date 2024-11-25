from imgui.integrations.glfw import imgui


class DisabledButton:
    def __enter__(self):
        imgui.push_item_flag(imgui.ITEM_DISABLED, True)
        imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha * 0.5)

    def __exit__(self):
        imgui.pop_item_flag()
        imgui.pop_style_var()
