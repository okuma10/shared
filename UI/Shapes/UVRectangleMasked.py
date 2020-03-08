import numpy as np
from ... import Image_loader
from bgl import *
from ...ExternalModules.pyrr import matrix44,Vector3,Vector4
from pathlib import Path

# find root dir
root_dir = None
ui_dir = None
tree_dir = Path(__file__).parents
for up_dir in tree_dir:
    if up_dir.name == "BlenderDrawDev":
        root_dir = up_dir
    elif up_dir.name == "UI":
        ui_dir = str(up_dir)
    else:pass
parent = str(root_dir)

class UVRectangleMasked:
    def __init__(self, size, program):
        self.state = 0
        self.idleColor      = Vector4([0.467, 0.549, 0.639, 1.0],dtype=np.float32)
        self.overColor      = Vector4([0.467, 0.549, 0.639, 1.0],dtype=np.float32)
        self.activeColor    = Vector4([0.467, 0.549, 0.639, 1.0],dtype=np.float32)
        #n Shader
        self.program = program
        #n Transforms
        self.parent     = Vector3([0,0,0])
        self.position   = Vector3([0, 0, 0])
        self.rotation   = Vector3([np.deg2rad(0),np.deg2rad(0),np.deg2rad(0)])
        self.scale      = Vector3([1, 1, 1])
        #n Textures
        self.maskTex = Image_loader.Texture(ui_dir + "/Shaders/textures/NUDGE.png")
        texture_dimensions = self.maskTex.getImageDimensions()
        #n Size
        self.h_width  = (texture_dimensions[0]*size)/2
        self.h_height = (texture_dimensions[1]*size)/2
        #n Data
        self.vertices = [
                            (0-self.h_width, 0-self.h_height, 0),
                            (0+self.h_width, 0-self.h_height, 0),
                            (0+self.h_width, 0+self.h_height, 0),
                            (0-self.h_width, 0+self.h_height, 0),
                            ]
        self.dimensions = [
                            self.vertices[2][0]-self.vertices[0][0],
                            self.vertices[2][1]-self.vertices[0][1]
                            ]
        uvs = [ (0, 0),
                (1, 0),
                (1, 1),
                (0, 1)]

        self.vertices=np.array(self.vertices, dtype=np.float32)
        uvs             =np.array(uvs, dtype=np.float32)
        vBsize      = self.vertices.nbytes+uvs.nbytes
        self.noP    = len(self.vertices)
        v_Buffer    = Buffer(GL_FLOAT, (self.noP, 3), self.vertices)
        uv_Buffer = Buffer(GL_FLOAT, (len(uvs), 2), uvs)

        #n VAO VBO
        self.VAO,self.VBO = Buffer(GL_INT, 1),Buffer(GL_INT, 1)
        glGenVertexArrays(1, self.VAO)
        glGenBuffers(1, self.VBO)
        #n  VBO setup
        glBindVertexArray(self.VAO[0])
        glBindBuffer(GL_ARRAY_BUFFER,self.VBO[0])
        glBufferData(GL_ARRAY_BUFFER, vBsize, None, GL_STATIC_DRAW)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, v_Buffer)
        glBufferSubData(GL_ARRAY_BUFFER, self.vertices.nbytes, uvs.nbytes, uv_Buffer)
        #n      Attributes
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, 0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 8, self.vertices.nbytes)
        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)



        #n Matricies
        self.m_matrix   = matrix44.create_identity(dtype=np.float32)
        self.t_matrix   = matrix44.create_from_translation(self.position, dtype=np.float32)
        self.r_matrix   = matrix44.create_from_eulers(self.rotation, dtype=np.float32)
        self.s_matrix   = matrix44.create_from_scale(self.scale, dtype=np.float32)
        self.view       = matrix44.create_identity(dtype=np.float32)
        self.proj       = matrix44.create_identity(dtype=np.float32)

    def draw(self,proj,view):
        #n2 temp!!!
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #n2 temp!!

        # print(f'time {}')
        self.view = view
        self.proj = proj
        mvp_matrix = matrix44.multiply(self.m_matrix, matrix44.multiply(view, proj))
        mvp_buffer = Buffer(GL_FLOAT,(4,4), mvp_matrix)


        self.program.activate()

        self.maskTex.Bind()
        if self.state == 0:
            self.program.setVec4('color', *self.idleColor)
        if self.state == 1:
            self.program.setVec4('color', *self.overColor)
        if self.state == 2:
            self.program.setVec4('color', *self.overColor)
            self.program.setVec3('color2', *self.activeColor[:3])

        self.program.setInt('state', self.state)
        self.program.setMat4('mvp', mvp_buffer)

        glBindVertexArray(self.VAO[0])

        glDrawArrays(GL_TRIANGLE_FAN,0,self.noP)

        glBindVertexArray(0)
        self.program.deactivate()

    def clear(self):
        glDeleteVertexArrays(1,self.VAO)
        glDeleteBuffers(1,self.VBO)


    def setPos(self, x, y, z):
        self.position = Vector3([x,y,z])
        pos_plus_parent = Vector3([self.parent.x + self.position.x, self.parent.y + self.position.y, z])
        self.t_matrix = matrix44.create_from_translation(pos_plus_parent, dtype = np.float32)

    def setParent(self,pX,pY,pZ):
        self.parent = Vector3([pX,pY,pZ])
        pos_plus_parent = Vector3([self.parent.x + self.position.x, self.parent.y + self.position.y, 0])
        self.t_matrix = matrix44.create_from_translation(pos_plus_parent, dtype=np.float32)

    def setRot(self, angX, angY, angZ):
        self.rotation = Vector3([np.deg2rad(angX),np.deg2rad(angY),np.deg2rad(angZ)])
        self.r_matrix= matrix44.create_from_eulers(self.rotation, dtype=np.float32)

    def setScale(self, scaleX, scaleY, scaleZ):
        self.scale = Vector3([scaleX, scaleY, scaleZ])
        self.s_matrix = matrix44.create_from_scale(self.scale, dtype=np.float32)

    def setColors(self,idle,over,active):
        self.idleColor = Vector4([*idle],dtype=np.float32)
        self.overColor = Vector4([*over],dtype=np.float32)
        self.activeColor = Vector4([*active],dtype=np.float32)

    def setState(self, state):
        self.state = state

    def updateMatrix(self):
        #model = scale * translate * rotate
        self.m_matrix = matrix44.multiply(self.s_matrix, matrix44.multiply(self.r_matrix, self.t_matrix))


    def getPositions(self):
        v_1 = self.vertices[0]
        v_2 = self.vertices[2]

        mV_1 =  Vector3 (matrix44.apply_to_vector(self.m_matrix, v_1))
        mV_2 =  Vector3(matrix44.apply_to_vector(self.m_matrix, v_2))

        return (mV_1, mV_2)