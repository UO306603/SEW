"""
@version 1.1 
@author: Andrés Fernández García
"""

import xml.etree.ElementTree as ET

class GeneradorSVG:
    
    def __init__(self, archivoXML, archivoSVG):
        """Inicializo los atributos de instancia en este metodo"""
        self.archivoXML = archivoXML
        self.archivoSVG = archivoSVG
        self.ns = {'uo': 'http://www.uniovi.es'}
        
        self.alto_maximo = 2000 
        self.svg = Svg(ancho=1000, alto=self.alto_maximo)
        
        """Cargo el arbol DOM del xml y creo la raiz"""
        try:
            self.arbolXML = ET.parse(self.archivoXML)
            self.raizXML = self.arbolXML.getroot()
        except IOError:
            print ('No se encuentra el archivo ', self.archivoXML)
            exit()
        except ET.ParseError:
            print("Error procesando en el archivo XML = ", self.archivoXML)
            exit()


    """Método auxiliar para extraer alt con XPath de un elemento del arbol xml"""
    def extraerAltitud(self, elemento_padre):
        alt = elemento_padre.find('./uo:coordenadas/uo:altitud', self.ns).text
        return float(alt)


    """Método que extrae toda la información del XML mediante XPath y genera los puntos"""
    def procesarAltimetria(self):
        puntos = []

        #Obtengo la longitud total de la etapa
        longitud_etapa = float(self.raizXML.find('./uo:longitud_etapa', self.ns).text)

        """Punto en la salida"""
        inicio = self.raizXML.find('./uo:inicio', self.ns)
        if inicio is not None:
            dist_salida = 0.0
            alt = self.extraerAltitud(inicio)
            nombre = inicio.find('./uo:ciudad', self.ns).text
            puntos.append((dist_salida, alt, nombre))

        """Puntos en los puertos de montaña"""
        puertos = self.raizXML.findall('.//uo:puerto_montana', self.ns)
        for p in puertos:
            dist_salida = float(p.find('./uo:distancia_salida', self.ns).text)
            alt = self.extraerAltitud(p)
            nombre = p.find('./uo:nombre_hito', self.ns).text
            puntos.append((dist_salida, alt, nombre))

        """Puntos en los sprints"""
        sprints = self.raizXML.findall('.//uo:sprint', self.ns)
        for s in sprints:
            dist_salida = float(s.find('./uo:distancia_salida', self.ns).text)
            alt = self.extraerAltitud(s)
            nombre = s.find('./uo:nombre_hito', self.ns).text
            puntos.append((dist_salida, alt, ""))

        """Puntos anónimos"""
        anonimos = self.raizXML.findall('.//uo:punto_anonimo', self.ns)
        for a in anonimos:
            dist_salida = float(a.find('./uo:distancia_salida', self.ns).text)
            alt = self.extraerAltitud(a)
            nombre_nodo = a.find('./uo:nombre_punto', self.ns)
            nombre = nombre_nodo.text if nombre_nodo is not None else ""
            puntos.append((dist_salida, alt, ""))

        """Punto en la meta"""
        meta = self.raizXML.find('./uo:meta', self.ns)
        if meta is not None:
            dist_salida = longitud_etapa
            alt = self.extraerAltitud(meta)
            nombre = meta.find('./uo:ciudad', self.ns).text
            puntos.append((dist_salida, alt, nombre))

        # Delegamos la ordenación y el pintado en el lienzo a un método auxiliar
        self.dibujarPerfil(puntos, longitud_etapa)


    """Método que se encarga del procesado matemático de los puntos para pintar la polilinea y de añadir los elementos al SVG"""
    def dibujarPerfil(self, puntos, longitud_etapa):

        #Ordenación del array de puntos para que se pinten en funcion de la distancia a la salida.
        puntos.sort(key=lambda p: p[0])

        ancho_svg = 1000
        alto_svg = self.alto_maximo
        margen_x = 50
        margen_y = 200 

        max_dist = longitud_etapa if longitud_etapa > 0 else 1.0
        
        altitudes = [p[1] for p in puntos]
        min_alt = min(altitudes)
        max_alt = max(altitudes)
        rango_alt = (max_alt - min_alt) if (max_alt - min_alt) > 0 else 1.0

        ancho_util = ancho_svg - (2 * margen_x)
        alto_util = alto_svg - (2 * margen_y)
        
        y_base = alto_svg - margen_y 

        puntos_escalados = []
        textos_a_dibujar = []

        for dist, alt, nombre in puntos:
            x = margen_x + (dist / max_dist) * ancho_util
            y = alto_svg - margen_y - ((alt - min_alt) / rango_alt) * alto_util
            puntos_escalados.append((x, y))
            
            if nombre:
                textos_a_dibujar.append((x, nombre))

        x_inicial = puntos_escalados[0][0]
        x_final = puntos_escalados[-1][0]
        
        puntos_poligono = []
        puntos_poligono.append((x_inicial, y_base)) 
        puntos_poligono.extend(puntos_escalados)    
        puntos_poligono.append((x_final, y_base))   
        puntos_poligono.append((x_inicial, y_base)) 

        puntos_str = " ".join([f"{x},{y}" for x, y in puntos_poligono])

        self.svg.addPolyline(puntos_str, "red", "4", "white")

        for x, nombre in textos_a_dibujar:
            self.svg.addText(nombre, x, y_base + 15, "sans-serif", "14", "writing-mode: tb; glyph-orientation-vertical: 0;")


    """Método que escribe el archivo SVG"""
    def escribirSVG(self):
        self.svg.escribir(self.archivoSVG)

    def generar(self):
        self.procesarAltimetria()
        self.escribirSVG()


class Svg(object):
    """
    Genera archivos SVG con rectángulos, círculos, líneas, polilíneas y texto
    """
    def __init__(self, ancho,alto):
        self.raiz = ET.Element('svg', 
                               xmlns="http://www.w3.org/2000/svg", 
                               version="2.0",
                               viewBox=f"0 0 {ancho} {alto}",
                               width="100%",
                               height="100%")

    def addPolyline(self, points, stroke, stroke_width, fill):
        """
        Añade un elemento polyline siguiendo estándares W3C
        """
        ET.SubElement(self.raiz, 'polyline',
                      points=points,
                      stroke=stroke,
                      attrib={'stroke-width': str(stroke_width)},
                      fill=fill)

    def addText(self,texto,x,y,fontFamily,fontSize,style):
            """
            Añade un elemento texto
            """
            ET.SubElement(self.raiz,'text',
                          x=str(x),
                          y=str(y),
                          fontFamily=fontFamily,
                          fontSize=fontSize,
                          style=style).text=texto

    def escribir(self, nombreArchivoSVG):
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        arbol.write(nombreArchivoSVG, 
                    encoding='utf-8', 
                    xml_declaration=True)


def main():
    print("Conversor de XML a SVG - Etapa Ciclista")
    miArchivoXML = input('Introduzca el archivo XML de origen: ')
    miArchivoSVG = input('Introduzca el nombre del archivo SVG a generar: ')
    
    generador = GeneradorSVG(miArchivoXML, miArchivoSVG)
    generador.generar()

if __name__ == "__main__":
    main()