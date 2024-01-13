#version 330 core

in vec2 v_Position;
in vec2 v_TexCoords;

out vec2 f_TexCoords;

void main() {
    f_TexCoords = v_TexCoords;
    gl_Position = vec4(v_Position, 0, 1);
}
