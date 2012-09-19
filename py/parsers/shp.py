import parsers.base as base, parsers.dbf as dbf
from parsers.base import Parser
from parsers.dbf import DbfParser
import json

class ShpParser(Parser):

    def __init__(self, filename):
        if not filename.endswith("shp"):
            dbffilename = filename + ".dbf"
            shpfilename = filename + ".shp"
        else:
            dbffilename = filename.split(".")[0] + ".dbf"
            shpfilename = filename

        Parser.__init__(self, shpfilename, base.LITTLE_ENDIAN)
        self.bbox = []

        self.features = []
        self.ignore_fields = []
        self.dbf_parser = DbfParser(dbffilename)

        self.shape_type = None
        self.last_read_type = None
        self.bbox_cache = None

        self.shape_types = {
            0: self.NullShape,
            1: self.Point,
            3: self.PolyLine,
            5: self.Polygon,
            8: self.MultiPoint,
            11: self.PointZ,
            13: self.PolyLineZ,
            15: self.PolygonZ,
            18: self.MultiPointZ,
            21: self.PointM,
            23: self.PolyLineM,
            25: self.PolygonM,
            28: self.MultiPointM,
            31: self.MultiPatch,
            }

    ### read methods from spec ###

    def read_point(self):
        x = self.read_double()
        y = self.read_double()
        self.last_read_type = "Point"
        return [x, y]

    def NullShape(self):
        self.last_read_type = "Null"

    def Point(self):
        return { "type": "Point", "coordinates": self.read_point() }

    def PolyLine(self):
        feature = {"coordinates": []}
        bbox = self.read_bbox()
        numparts = self.read_word(4)
        numpoints = self.read_word(4)

        if numparts == 1:
            feature["type"] = "LineString"
            while numpoints > 0:
                feature["coordinates"].append(self.read_point())
                numpoints -= 1
        else:
            feature["type"] = "MultiLineString"
            parts = []
            while numparts > 0:
                parts.append(self.read_word(4))
                numparts -= 1
            arrindex = 0
            points = []
            
            while numpoints > 0:
                if arrindex in parts:
                    points = []
                    feature["coordinates"].append(points) # pointer magic
                points.append(self.read_point())
                numpoints -= 1
                arrindex += 1

        return feature

    # from spec:
    # "The neighborhood to the right of an observer walking along
    # the ring in vertex order is the neighborhood inside the polygon."
    def Polygon(self):
        feature = {
            "type": "Polygon",
            "coordinates": [],
            }

        self.bbox_cache = self.read_bbox()
        numrings = self.read_word(4)
        numpoints = self.read_word(4)

        rings = []
        while numrings > 0:
            rings.append(self.read_word(4))
            numrings -= 1
      
        arrindex = 0
        points = []
        while numpoints > 0:
            if arrindex in rings:
                points = []
                feature["coordinates"].append(points)
            points.append(self.read_point())
            numpoints -= 1
            arrindex += 1

        return feature

    def MultiPoint(self):
        bbox = self.read_bbox()
        numpoints = self.read_word(4)
        points = []
        while (numpoints > 0):
            points.append(self.read_point())
            numpoints -= 1
        return {
            "type": "MultiPoint",
            "coordinates": points,
            }
        
    def PointZ(self): return
    def PolyLineZ(self): return
    def PolygonZ(self): return
    def MultiPointZ(self): return
    def PointM(self): return
    def PolyLineM(self): return
    def PolygonM(self): return
    def MultiPointM(self): return
    def MultiPatch(self): return

    def read_bbox(self):
        bbox = []
        for i in range(4):
            bbox.append(self.read_double())
        return bbox

    ############### main (.shp) file header description ############
    # Byte  Field         Value        Type     Order
    # 0     File Code     9994         Integer  Big
    # 4     Unused        0            Integer  Big
    # 8     Unused        0            Integer  Big
    # 12    Unused        0            Integer  Big
    # 16    Unused        0            Integer  Big
    # 20    Unused        0            Integer  Big
    # 24    File Length   File Length  Integer  Big
    # 28    Version       1000         Integer  Little
    # 32    Shape Type    Shape Type   Integer  Little
    # 36    Bounding Box  Xmin         Double   Little
    # 44    Bounding Box  Ymin         Double   Little
    # 52    Bounding Box  Xmax         Double   Little
    # 60    Bounding Box  Ymax         Double   Little
    # 68*   Bounding Box  Zmin         Double   Little
    # 76*   Bounding Box  Zmax         Double   Little
    # 84*   Bounding Box  Mmin         Double   Little
    # 92*   Bounding Box  Mmax         Double   Little
    #################################################################
    def read_header(self):
        if self.position > 0:
            raise Exception("header already read")

        if self.read_word(4, base.BIG_ENDIAN) != 9994:
            raise Exception("incorrect header values")
    
        self.skipto(24)
        self.file_length = self.read_word(4, base.BIG_ENDIAN) * self.WORDSIZE
        self.skipto(32)
        self.shape_type = self.read_word(4)
        self.bbox = self.read_bbox()

        self.skipto(100)

        self.dbf_parser.read_header()

    def add_ignore_fields(self, fieldlist):
        self.ignore_fields = fieldlist

    ############### main (.shp) file record headers #################
    # Byte  Field           Value           Type     Order
    # 0     Record Number   Record Number   Integer  Big
    # 4     Content Length  Content Length  Integer  Big
    #################################################################
    def read_record(self):
        rec_no = self.read_word(4, base.BIG_ENDIAN)
        rec_length = self.read_word(4, base.BIG_ENDIAN)
        read_shape = self.shape_types[self.read_word(4)]
        properties = self.dbf_parser.read_record()

        for field in self.ignore_fields:
            del properties[field]

        feature = {
            "type": "Feature",
            "geometry": read_shape(),
            "properties": properties
            }

        if self.bbox_cache is not None:
            feature["bbox"] = self.bbox_cache
            self.bbox_cache = None

        return feature

    def read_all_records(self):
        while self.position < self.file_length:
            self.features.append(self.read_record())
 
    def write_json(self, filename):
        outfile = open(filename, 'w')
        outfile.write(json.dumps({
            "type": "FeatureCollection",
            "bbox": self.bbox,
            "features": self.features,
            }))
        outfile.close()
        print("new json file written to", filename)

    def join_data(join_field, iterable_data):
        data = {}
        for row in iterable_data:
            row_id = row[join_field]
            del row[join_field]
            data[row_id] = row
        for feature in self.features:
            attribs = data[feature[join_field]]
            for (attrib_name, attrib_value) in attribs.items():
                feature["properties"][attrib_name] = attrib_value
