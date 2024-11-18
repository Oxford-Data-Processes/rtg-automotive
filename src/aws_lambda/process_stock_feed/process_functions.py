def get_value_if_less_than_10_else_0(x):
    return max(0, min(x, 10)) if isinstance(x, (int, float)) and x > 0 else 0


def set_value_to_10_if_product_in_list(x):
    return 10


def set_value_to_10_if_labelled_in_stock(x):
    if x.lower() in ["in stock"]:
        return 10
    else:
        return 0


def set_value_to_10_if_labelled_yes(x):
    if "y" in x.lower():
        return 10
    else:
        return 0


def return_value(x):
    return x


def create_function(func_str):
    return eval(func_str) if func_str.startswith("lambda") else globals().get(func_str)
