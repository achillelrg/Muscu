import matplotlib.colors as mc
import colorsys

def adjust_lightness(color, amount=0.5):
    """
    Adjusts the lightness of the given color.
    
    Args:
        color (str): Hex color or matplotlib color name.
        amount (float): Factor to adjust lightness. <1 makes it darker, >1 makes it lighter (up to a limit).
                        Actually logic: amount * lightness. 
                        Usually we want 0.5 to darken, 1.5 to lighten.
                        Wait, previous logic was: max(0, min(1, amount * l)).
                        If amount < 1.0, it darkens. If amount > 1.0, it lightens.
    """
    try:
        c = mc.cnames.get(color, color) # Try to get from cnames, else assume hex/other
        c = colorsys.rgb_to_hls(*mc.to_rgb(c))
        
        # New lightness
        new_l = max(0, min(1, amount * c[1]))
        
        return mc.to_hex(colorsys.hls_to_rgb(c[0], new_l, c[2]))
    except Exception as e:
        print(f"Error adjusting color {color}: {e}")
        return color # Fallback
