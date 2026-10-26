"""
@version 1.0 
@author: Andrés Fernández García
"""

import xml.etree.ElementTree as ET

class GeneradorKML:
    
    def __init__(self, archivoXML, archivoKML):

        """Inicializo los atributos de instancia en este metodo"""
        self.archivoXML = archivoXML
        self.archivoKML = archivoKML
        self.ns = {'uo': 'http://www.uniovi.es'}
        
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
            
        """Creo la raiz del arbol kml junto con la etiqueta "Document". """
        self.raizKML = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
        self.docKML = ET.SubElement(self.raizKML, 'Document')

    """Método para añadir un punto especifico al kml"""
    def addPlacemark(self, nombre, descripcion, long, lat, alt, modoAltitud, color):
        pm = ET.SubElement(self.docKML, 'Placemark')
        ET.SubElement(pm, 'name').text = nombre
        ET.SubElement(pm, 'description').text = descripcion
        
        estilo = ET.SubElement(pm, 'Style')
        icono = ET.SubElement(estilo, 'IconStyle')
        ET.SubElement(icono, 'color').text = color
        
        punto = ET.SubElement(pm, 'Point')
        ET.SubElement(punto, 'coordinates').text = f'{long},{lat},{alt}'
        ET.SubElement(punto, 'altitudeMode').text = modoAltitud

    """Método para añadir una linea de ruta al kml""" 
    def addLineString(self, nombre, extrude, tesela, listaCoordenadas, modoAltitud, color, ancho):
        """Añade la línea de la ruta (LineString) al KML"""
        pm = ET.SubElement(self.docKML, 'Placemark')
        ET.SubElement(pm, 'name').text = nombre
        
        ls = ET.SubElement(pm, 'LineString')
        ET.SubElement(ls, 'extrude').text = extrude
        ET.SubElement(ls, 'tessellate').text = tesela
        ET.SubElement(ls, 'coordinates').text = listaCoordenadas
        ET.SubElement(ls, 'altitudeMode').text = modoAltitud 

        # Estilo de la línea
        estilo = ET.SubElement(pm, 'Style')
        linea = ET.SubElement(estilo, 'LineStyle')
        ET.SubElement(linea, 'color').text = color
        ET.SubElement(linea, 'width').text = ancho

    """Método auxiliar para extraer lon, lat y alt con XPath de un elemento del arbol xml"""
    def extraerCoordenada(self, elemento_padre):
        lon = elemento_padre.find('./uo:coordenadas/uo:longitud_geo', self.ns).text
        lat = elemento_padre.find('./uo:coordenadas/uo:latitud_geo', self.ns).text
        alt = elemento_padre.find('./uo:coordenadas/uo:altitud', self.ns).text
        return lon, lat, alt

    """Método que extrae toda la información del XML mediante XPath y la añade al KML"""
    def procesarPlanimetria(self):
        """Creacion de las lineas de rutas obteniendo mediante XPath todos los atributos coordenadas del XML sin importar la profundidad en el arbol del elemento padre"""
        coordenadas = self.raizXML.findall('.//uo:coordenadas', self.ns)
        lista_coords = []
        for c in coordenadas:
            lon = c.find('./uo:longitud_geo', self.ns).text
            lat = c.find('./uo:latitud_geo', self.ns).text
            alt = c.find('./uo:altitud', self.ns).text
            lista_coords.append(f"{lon},{lat},{alt}")
        
        coords_str = "\n".join(lista_coords)
        self.addLineString("Ruta de la etapa", "1", "1", coords_str, "clampToGround", "ff0000ff", "5")

        """Punto en la salida"""
        inicio = self.raizXML.find('./uo:inicio', self.ns)
        if inicio is not None:
            ciudad_ini = inicio.find('./uo:ciudad', self.ns).text
            lon, lat, alt = self.extraerCoordenada(inicio)
            self.addPlacemark(f"Salida: {ciudad_ini}", "Inicio de etapa", lon, lat, alt, "clampToGround", "ff0000ff")

        """Punto en la meta"""
        meta = self.raizXML.find('./uo:meta', self.ns)
        if meta is not None:
            ciudad_meta = meta.find('./uo:ciudad', self.ns).text
            lon, lat, alt = self.extraerCoordenada(meta)
            self.addPlacemark(f"Meta: {ciudad_meta}", "Fin de etapa", lon, lat, alt, "clampToGround", "ff0000ff")

        """Puntos en los puertos de montaña"""
        puertos = self.raizXML.findall('.//uo:puerto_montana', self.ns)
        for p in puertos:
            nombre = p.find('./uo:nombre_hito', self.ns).text
            lon, lat, alt = self.extraerCoordenada(p)
            self.addPlacemark(nombre, "Puerto de Montaña", lon, lat, alt, "clampToGround", "ff00ff00")

        """Puntos en los sprints"""
        sprints = self.raizXML.findall('.//uo:sprint', self.ns)
        for s in sprints:
            nombre = s.find('./uo:nombre_hito', self.ns).text
            lon, lat, alt = self.extraerCoordenada(s)
            self.addPlacemark(nombre, "Sprint Intermedio", lon, lat, alt, "clampToGround", "ffff0000")

        """Puntos anónimos"""
        anonimos = self.raizXML.findall('.//uo:punto_anonimo', self.ns)
        for i, a in enumerate(anonimos):
            lon, lat, alt = self.extraerCoordenada(a)
            self.addPlacemark(f"Punto {i+1}", "Punto Anónimo", lon, lat, alt, "clampToGround", "ff00ffff")

    """Método que escribe el archivo KML"""
    def escribirKML(self):
        arbolKML = ET.ElementTree(self.raizKML)
        if hasattr(ET, 'indent'):
            ET.indent(arbolKML)
            
        try:
            arbolKML.write(self.archivoKML, encoding='utf-8', xml_declaration=True)
            print(f"Éxito: Se ha generado el archivo '{self.archivoKML}' correctamente.")
        except IOError:
            print("Error: No se pudo escribir el archivo ", self.archivoKML)
            exit()


    def generar(self):
        self.procesarPlanimetria()
        self.escribirKML()


def main():
    print("Conversor de XML a KML - Etapa Ciclista")
    
    miArchivoXML = input('Introduzca el archivo XML de origen: ')
    miArchivoKML = input('Introduzca el nombre del archivo KML a generar: ')
    
    """Instancia de la clase generador"""
    generador = GeneradorKML(miArchivoXML, miArchivoKML)
    
    generador.generar()

if __name__ == "__main__":
    main()