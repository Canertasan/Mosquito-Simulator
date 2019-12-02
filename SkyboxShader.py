from typing import Iterable

from OpenGL import GL as gl
from OpenGL.GL import shaders
from GameUtilities import *


class SkyboxShader:
    def __init__(self, cube_obj_data: ObjData):
        self.cube_obj_data = cube_obj_data

        # Compile shaders
        vertex_shader = shaders.compileShader("""#version 330
        layout(location = 0) in vec3 vertex_position;
        uniform mat4 projection;
        uniform mat4 view;

        out vec3 texture_position;

        void main()
        {
            //  Because the transformation matrix is 4x4, we have to construct a vec4 from position, so we an multiply them
            vec4 pos = vec4(vertex_position, 1.0);
            gl_Position = projection * view * pos;

            texture_position = vertex_position;
        }
        """, gl.GL_VERTEX_SHADER)

        fragment_shader = shaders.compileShader("""#version 330
        uniform samplerCube skybox_sampler;
        in vec3 texture_position;

        out vec4 fragment_color;

        void main()
        {
           // fragment_color = vec4(texture_position, 0.0);
             fragment_color = texture(skybox_sampler, texture_position);
        }
        """, gl.GL_FRAGMENT_SHADER)

        # Compile the program
        self.id = shaders.compileProgram(vertex_shader, fragment_shader)

        # Get the locations
        gl.glUseProgram(self.id)
        self.view_location = gl.glGetUniformLocation(self.id, "view")
        self.projection_location = gl.glGetUniformLocation(self.id, "projection")

        self.skybox_sampler = gl.glGetUniformLocation(self.id, "skybox_sampler")
        gl.glUniform1i(self.skybox_sampler, 0)
        gl.glUseProgram(0)

    def draw(self, projection, view, skybox_texture: int):
        gl.glUseProgram(self.id)

        gl.glUniformMatrix4fv(self.projection_location, 1, False, glm.value_ptr(projection))
        gl.glUniformMatrix4fv(self.view_location, 1, False, glm.value_ptr(view))

        # Set the vao
        gl.glBindVertexArray(self.cube_obj_data.vao)

        for mesh in self.cube_obj_data.meshes:
            # Set skybox texture
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, skybox_texture)

            # Draw the mesh with an element buffer.
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, mesh.element_array_buffer)
            # When the last parameter in 'None', the buffer bound to the GL_ELEMENT_ARRAY_BUFFER will be used.
            gl.glDrawElements(gl.GL_TRIANGLES, mesh.element_count, gl.GL_UNSIGNED_INT, None)
