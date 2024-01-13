#version 330 core

uniform sampler2D entity;
uniform sampler2D ui;

in vec2 f_TexCoords;
out vec4 f_Color;

vec4 merge(vec4 e_Tex, vec4 u_Tex) {
    if (u_Tex.rgb == vec3(0, 0, 0)) {
        return e_Tex;
    }

    return u_Tex * u_Tex.a + e_Tex * (1.0 - u_Tex.a);
}

void main() {
    vec4 e_Tex = texture(entity, f_TexCoords);
    vec4 u_Tex = texture(ui, vec2(f_TexCoords.x, f_TexCoords.y));

    f_Color = merge(e_Tex, u_Tex);
}
