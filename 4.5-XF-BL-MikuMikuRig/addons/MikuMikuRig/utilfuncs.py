import bpy

def get_state():
    if bpy.context.scene.mmr_kumopult_bac_owner is None:
        return None
    return bpy.context.scene.mmr_kumopult_bac_owner.data.mmr_kumopult_bac


def set_enable(con: bpy.types.Constraint, state):
    if bpy.app.version >= (3, 0, 0):
        con.enabled = state
    else:
        con.mute = not state