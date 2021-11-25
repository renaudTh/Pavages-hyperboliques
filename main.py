import cmath
import math
import time

from PIL import Image, ImageDraw
import Window_Model as WinMod


def det(zA, zB, prec=1e-12):
    d = zA.real * zB.imag - zA.imag * zB.real
    if abs(d) < prec:
        return 0
    else:
        return d


def change_angle(alpha):
    if alpha < 0:
        alpha = -alpha
    else:
        alpha = 2 * math.pi - alpha
    return alpha


def conj(z):
    return z.real - z.imag * 1j


def circle_box(window, center, radius):
    zmin = window.picture_coordinates(center - radius * (1 - 1j))
    zmax = window.picture_coordinates(center + radius * (1 - 1j))
    return zmin, zmax


def hyperbolic_circle(zA, zB):
    a = (zA.imag * (1 + abs(zB) ** 2) - zB.imag * (1 + abs(zA) ** 2)) / det(zA, zB)
    b = (zB.real * (1 + abs(zA) ** 2) - zA.real * (abs(zB) ** 2 + 1)) / det(zA, zB)
    zI = -a / 2 - b / 2 * 1j
    r = math.sqrt(abs(a ** 2 / 4 + b ** 2 / 4 - 1))
    return zI, r


def draw_hyperbolic_arc(surface, window, zA, zB, color=(255, 0, 0), thickness=12):
    if det(zA, zB) == 0:
        surface.line([window.picture_coordinates(zA), window.picture_coordinates(zB)], color, thickness)
    else:
        zI, r = hyperbolic_circle(zA, zB)
        alpha1 = cmath.phase(zA - zI)
        alpha2 = cmath.phase(zB - zI)
        alpha1, alpha2 = change_angle(alpha1), change_angle(alpha2)
        minimum = min(alpha1, alpha2)
        maximum = max(alpha1, alpha2)
        if maximum - minimum > math.pi:
            alpha1, alpha2 = maximum, minimum
        else:
            alpha1, alpha2 = minimum, maximum
        surface.arc(circle_box(window, zI, r), alpha1 * 180 / math.pi, alpha2 * 180 / math.pi, color, thickness)


def draw_broken_line(surface, window, points, color="red", thickness=12):
    k = 0
    while k < len(points):
        draw_hyperbolic_arc(surface, window, points[k - 1], points[k], color, thickness)
        k = k + 1


def draw_point(surface, window, z, color, thickness=0):
    if thickness == 0:
        surface.point(window.picture_coordinates(z), color)
    else:
        box = circle_box(window,z,0.008)
        surface.ellipse(box, color)


def inversion(zA, zB, z):
    if det(zA, zB) == 0:
        a = (zB - zA) / (conj(zB) - conj(zA))
        return a * conj(z - zA) + zA
    else:
        zI, r = hyperbolic_circle(zA, zB)
        return zI + r ** 2 / conj(z - zI)


def polygone_initial(n, p):
    r = math.sin(math.pi / n) / math.sqrt(math.cos(math.pi / p) ** 2 - math.sin(math.pi / n) ** 2)
    z0 = r * math.cos(math.pi / n + math.pi / p) / math.sin(math.pi / n) * cmath.exp(1j * math.pi / n)
    liste_sommets = []
    for k in range(0, n):
        z1 = z0 * cmath.exp(-2 * 1 * 1j * math.pi / n)
        liste_sommets.append(z1)
        z0 = z1
    return liste_sommets


def draw_canonical_tilling(surface, window, n, p, ordre=5, color="black"):
    poly = [Polygone(window, polygone_initial(n, p))]
    for k in range(ordre):
        new_poly = []
        for p in poly:
            vertices = set(p.get_vertices())
            for v in vertices:
                new_p = p.inversion(v)
                new_poly.append(new_p)
                new_p.trace(surface, color, factor * 1)
        poly = new_poly



class Polygone:
    def __init__(self, window, listePoints):
        self.sommets = listePoints
        self.window = window
        self.nb_cotes = len(self.sommets)

    def trace(self, surface, color="red", thickness=12):
        for k in range(self.nb_cotes):
            draw_hyperbolic_arc(surface, window, self.sommets[k - 1], self.sommets[k], color, thickness)

    def is_convex(self):
        somme = 0
        for k in range(self.nb_cotes):
            somme = somme + cmath.phase(self.sommets[k] - self.sommets[k - 1])
        return somme < math.pi

    def get_nb_cotes(self):
        return self.nb_cotes

    def get_vertices(self):
        return [(self.sommets[k], self.sommets[k - 1]) for k in range(self.nb_cotes)]

    def inversion(self, arete):
        arete = list(arete)
        inverse = [inversion(arete[0], arete[1], s) for s in self.sommets]
        return Polygone(window, inverse)

    def is_inside(self, affixe):
        x = affixe.real
        y = affixe.imag
        vertices = self.get_vertices()
        count = 0
        for v in vertices:
            if det(v[0], v[1]) != 0:
                zC, R = hyperbolic_circle(v[0], v[1])
                if abs(zC-affixe)>R:
                    count = count+1
            else:
                count = count+1
        return count == self.nb_cotes

    def bounding_box(self):
        real = [s.real for s in self.sommets]
        im = [s.imag for s in self.sommets]
        zmin = min(real)+1j*min(im)
        zmax = max(real)+1j*max(im)
        return zmin, zmax

    def fill(self, surface, color):
        (zmin, zmax) = self.bounding_box()
        i = zmin.real
        while i < zmax.real:
            j = zmin.imag
            while j < zmax.imag:
                if self.is_inside(i + j * 1j):
                    draw_point(surface, self.window, i + 1j * j, color)
                j = j + self.window.p_y()
            i = i + self.window.p_x()



if __name__ == '__main__':
    start_time = time.time()

    real_width = 400
    real_height = 400
    factor = 4
    eps = 1.2
    image = Image.new("RGB", (factor * real_width, factor * real_height), (255, 255, 255))
    window = WinMod.Window(-eps, -eps, eps, eps, factor * real_width, factor * real_height)
    surface = ImageDraw.Draw(image)
    surface.ellipse(circle_box(window, 0 + 0 * 1j, 1), None, (0, 0, 0), 2 * factor)

    draw_canonical_tilling(surface, window,5,4)

    image_resized = image.resize((real_width, real_height), Image.ANTIALIAS)
    image_resized.show()
    image_resized.save("cercle.png", "PNG")
print("Temps d execution : %s secondes ---" % (time.time() - start_time))
