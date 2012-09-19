import math
from scipy import sparse
from common.dbhelper import db

def mult_numpy_matrices(multiplicand, multiplier):
    if not sparse.issparse(multiplicand):
        multiplicand = sparse.csr_matrix(multiplicand)
    else:
        multiplicand = multiplicand.tocsr()
    if not sparse.issparse(multiplier):
        multiplier = sparse.csr_matrix(multiplier)
    else:
        multiplier = multiplier.tocsr()

    return multiplicand * multiplier

class NamedMatrix:

    # square in this case means the columns and rows represent the same
    # thing, so we only need one set of names.
    # if cols/rows represent different things but happen to be the same
    # length, square would be False here
    def __init__(self, square=False, from_matrix=None, rows=[], cols=[]):
        if from_matrix is not None and not sparse.issparse(from_matrix):
            self.matrix = sparse.lil_matrix(from_matrix)
        else:
            self.matrix = from_matrix
        self.square = square
        self.harmonized_rows = {}
        self.set_rows(rows)
        if not self.square:
            self.harmonized_cols = {}
            self.set_columns(cols)

    def get_diag(self):
        if not self.square:
            raise Exception("cannot get diag of non-square matrix")

        matrix = NamedMatrix(square=False, rows=self.get_rows(), cols=["value"])
        for row in self.get_rows():
            matrix.set_element(row, "value", self.get_element(row, row))

        return matrix

    def square_matrix_from_diag(self):
        cols = self.get_columns()
        rows = self.get_rows()
        matrix = None
        if len(cols) == 1:
            col = cols[0]
            matrix = NamedMatrix(square=True, rows=rows)
            for row in rows:
                matrix.set_element(row, row, self.get_element(row, col))
        elif len(rows) == 1:
            row = rows[0]
            matrix = NamedMatrix(square=True, rows=cols)
            for col in cols:
                matrix.set_element(col, col, self.get_element(row, col))
        else:
            raise Exception("cannot use square_matrix_from_diag on non-vector")

        return matrix

    # these getter methods are here for overriding
    def mat(self):
        return self.matrix

    def get_rows(self):
        return self.rows

    def get_columns(self):
        if self.square:
            return self.rows
        return self.cols

    def get_submatrix(self, rows=None, cols=None):
        rowindices = []
        colindices = []
        if rows is not None:
            for row in rows:
                rowindices.append(self.row_index(row))
        if cols is not None:
            for col in cols:
                colindices.append(self.col_index(col))

        if rows is None:
            if cols is None:
                matrix = self.matrix
            else:
                matrix = self.matrix[:, colindices]
        elif cols is None:
            matrix = self.matrix[rowindices, :]
        else:
            matrix = self.matrix[rowindices, colindices]

        if rows is None:
            rows = self.rows
        if cols is None:
            cols = self.cols

        return NamedMatrix(False, matrix, rows, cols)

    def get_named_column(self, column):
        colindex = self.rev_columns[column]
        colmatrix = self.matrix[:, colindex]
        return NamedMatrix(
            square=False,
            rows=self.get_rows(),
            cols=[column],
            from_matrix=colmatrix)

    def check_shape(self, other):
        return self.nrows() == other.nrows() and self.ncols() == other.ncols()

    def verify_mult_shape(self, other):
        if self.ncols() != other.nrows():
            dims = (self.nrows(), self.ncols(), other.nrows(), other.ncols())
            ourset = set(self.get_columns())
            theirset = set(other.get_rows())
            print(list(ourset.difference(theirset)) + \
                  list(theirset.difference(ourset)))
            raise Exception("matrix dimensions don't match " + \
                            "(attempted to multiply %dx%d by %dx%d)" % dims)

    def dims(self):
        return (self.nrows(), self.ncols())

    def nrows(self):
        return len(self.rows)

    def ncols(self):
        if self.square:
            return len(self.rows)
        return len(self.cols)

    # return a new matrix that is us post-multiplied by them
    def matrix_mult(self, other):
        self.verify_mult_shape(other)

        M = NamedMatrix(False)
        M.set_rows(self.get_rows())
        M.set_columns(other.get_columns())
        M.matrix = mult_numpy_matrices(self.mat(), other.mat())
        return M

    def matrix_postmult(self, other):
        other.verify_mult_shape(self)

        M = NamedMatrix(False)
        M.set_rows(other.get_rows())
        M.set_columns(self.get_columns())
        M.matrix = mult_numpy_matrices(other.mat(), self.mat())
        return M

    def transposed(self):
        matrix = self.matrix.transpose()
        M = NamedMatrix(
            square=self.square,
            from_matrix=self.matrix.transpose(),
            rows=self.get_columns(),
            cols=self.get_rows())

        if self.square:
            M.set_harmonized_rows(self.harmonized_rows)
        else:
            M.set_harmonized_rows(self.harmonized_cols)
            M.set_harmonized_cols(self.harmonized_rows)

        return M

    ### mutating functions
    def matrix_postmult_inplace(self, other):
        other.verify_mult_shape(self)
        self.matrix = mult_numpy_matrices(other.mat(), self.mat())
        self.set_rows(other.get_rows())
        return self

    def matrix_mult_inplace(self, other):
        self.verify_mult_shape(other)
        self.matrix = mult_numpy_matrices(self.mat(), other.mat())
        self.set_column(other.get_columns())
        return self

    def scalar_mult_inplace(self, scalar):
        self.matrix = self.matrix * scalar
        return self

    # return a new matrix point-wise multiplied by them
    def mult(self, other):
        return self._arith_helper(other, "multiply")

    # return a new matrix that is us divided by them
    def divide(self, other, ignore_zero_denom=False):
        if ignore_zero_denom:
            result = self._arith_helper(other, "divide", ["remove_inf"])
        else:
            result = self._arith_helper(other, "divide")
        return result

    def add(self, other):
        return self._arith_helper(other, "add")

    def subtract(self, other):
        return self._arith_helper(other, "subtract")

    def _arith_helper(self, other, operation, options=[]):
        if not self.check_shape(other):
            dims = (self.nrows(), self.ncols(), other.nrows(), other.ncols())
            raise Exception("matrix dimensions don't match" + \
                            "(operands: %dx%d, %dx%d)" % dims)

        M = NamedMatrix(self.square)
        M.set_rows(self.get_rows())
        if not self.square:
            M.set_columns(self.get_columns())

        if operation == "divide":
            matrix = self.mat() / other.mat()
            if "remove_inf" in options:
                (rows, cols) = matrix.nonzero()
                for (row, col) in zip(rows, cols):
                    if math.isinf(matrix[row, col]):
                        matrix[row, col] = 0
        elif operation == "multiply":
            multiplicand = self.mat()
            if not sparse.issparse(multiplicand):
                multiplicand = sparse.lil_matrix(multiplicand)
            matrix = multiplicand.multiply(other.mat())
        elif operation == "add":
            matrix = self.mat() + other.mat()
        elif operation == "subtract":
            matrix = self.mat() - other.mat()

        M.matrix = matrix

        return M

    def print(self, rowrange=None, colrange=None):
        if rowrange is None:
            rowrange = range(self.nrows())
        if colrange is None:
            if self.square:
                colrange = range(self.nrows())
            else:
                colrange = range(self.ncols())

        matrix = self.mat()
        columns = self.get_columns()
        rows = self.get_rows()
        for row in rowrange:
            for col in colrange:
                if matrix[row, col] != 0:
                    print(rows[row], columns[col], matrix[row, col])

    def set_harmonized_rows(self, harmonized):
        self.harmonized_rows = harmonized

    def get_harmonized_rowname(self, rowname):
        if rowname in self.rev_rows:
            return rowname
        if rowname in self.harmonized_rows:
            return self.harmonized_rows[rowname]
        return rowname

    def set_harmonized_cols(self, harmonized):
        self.harmonized_cols = harmonized

    def get_harmonized_colname(self, colname):
        if self.square:
            return self.get_harmonized_rowname(colname)
        if colname in self.harmonized_cols:
            return self.harmonized_cols[colname]
        return colname

    def has_row(self, row):
        return row in self.rev_rows

    def has_column(self, column):
        return column in self.rev_columns

    def set_rows(self, rows):
        if self.matrix is not None and self.matrix.shape[0] != len(rows):
            raise Exception(
                "number of rows (%d) doesn't match existing matrix (%dx%d)"
                % (len(rows), self.matrix.shape[0], self.matrix.shape[1]))

        self.rows = []     # list of row names
        self.rev_rows = {} # index number for each row name
        for row in rows:
            self.rev_rows[row] = len(self.rows)
            self.rows.append(row)

    def set_columns(self, columns):
        if self.square:
            raise Exception("set_columns doesn't work with 'square' option")

        if self.matrix is not None and self.matrix.shape[1] != len(columns):
            raise Exception("number of columns (%d) doesn't match " + \
                                "existing matrix (%dx%d)"
                            % (len(columns),
                               self.matrix.shape[0], self.matrix.shape[1]))

        self.cols = []     # list of column names
        self.rev_columns = {} # index number for each column name
        for col in columns:
            self.rev_columns[col] = len(self.cols)
            self.cols.append(col)

    def row_index(self, rowname):
        harmonized_rowname = self.get_harmonized_rowname(rowname)
        if harmonized_rowname not in self.rev_rows:
            print(sorted(self.rev_rows))
        return self.rev_rows[harmonized_rowname]

    def col_index(self, colname):
        if self.square:
            colindex = self.row_index(colname)
        else:
            harmonized_colname = self.get_harmonized_colname(colname)
            colindex = self.rev_columns[harmonized_colname]
        return colindex

    def sum(self, dimension=None):
        if dimension is None:
            return self.mat().sum()
        else:
            matrix = self.mat().sum(dimension)
            if dimension == 0:
                m = NamedMatrix(rows=["sum"], cols=self.get_columns(),
                                from_matrix=matrix)
            else:
                m = NamedMatrix(rows=self.get_rows(), cols=["sum"],
                                from_matrix=matrix)
            return m

    def get_element(self, rowname=None, colname=None):
        if rowname is None and colname is None:
            if self.nrows() == 1 and self.ncols() == 1:
                return self.matrix[0, 0]
            else:
                raise Exception("rowname or colname must be defined")

        if rowname is not None:
            rowindex = self.row_index(rowname)
            if colname is not None:
                colindex = self.col_index(colname)
                return self.matrix[rowindex, colindex]
            else:
                if self.ncols() == 1:
                    return self.matrix[rowindex, 0]
                return self.matrix[rowindex, :]

        # by now we know rowname is None, colname is not None
        if self.nrows() == 1:
            return self.matrix[0, colindex]
        return self.matrix[:, colindex]

    def set_column(self, colname, arg):
        colindex = self.col_index(colname)
        if self.matrix is None:
            self.matrix = sparse.lil_matrix(self.dims())
        elif type(self.matrix) is sparse.csr_matrix:
            self.matrix = self.matrix.tolil()

        if type(arg) is NamedMatrix:
            column = arg.mat()
            for i in range(self.matrix.shape[0]):
                self.matrix[i, colindex] = column[i, 0]
        elif type(arg) is int or type(arg) is float:
            for i in range(self.matrix.shape[0]):
                self.matrix[i, colindex] = arg


    def set_element(self, rowname, colname, value):

        if value is None:
            return

        if self.matrix is None:
            self.matrix = sparse.lil_matrix(self.dims())
        elif type(self.matrix) is sparse.csr_matrix:
            self.matrix = self.matrix.tolil()

        rowindex = self.row_index(rowname)
        colindex = self.col_index(colname)
        self.matrix[rowindex, colindex] = float(value)

def generate_selector_matrix(tablename, rows, row_field, col_field,
                             conditions=[]):

    whereclause = ""
    if len(conditions):
        whereclause = "WHERE " + " AND ".join(conditions)
 
    cols = []

    sql = "SELECT DISTINCT %s FROM %s %s" % (col_field, tablename, whereclause)
    stmt = db.prepare(sql)

    for row in stmt():
        if row[0] not in cols:
            cols.append(row[0])

    cols = sorted(cols)
    sel = NamedMatrix(square=False)

    # we want our columns to match their rows
    sel.set_rows(cols)
    sel.set_columns(rows)

    sql = "SELECT %s, %s FROM %s %s" % (
        row_field, col_field, tablename, whereclause)
    stmt = db.prepare(sql)

    for retrieved_row in stmt():
        if retrieved_row[0] in rows:
            sel.set_element(retrieved_row[1], retrieved_row[0], 1)

    return sel

class TotalOutputMatrix(NamedMatrix):

    def __init__(self, from_matrix=None, rows=[]):
        NamedMatrix.__init__(self, square=False,
                             from_matrix=from_matrix,
                             rows=rows,
                             cols=["Total Output"])

    def set_output(self, sector, value):
        self.set_element(sector, "Total Output", value)

    def get_output(self, sector):
        return self.get_element(sector, "Total Output")

class FinalDemandMatrix(NamedMatrix):

    def __init__(self, pce_colname, export_colname,
                 from_matrix=None, rows=[], cols=[]):

        NamedMatrix.__init__(self, square=False,
                             from_matrix=from_matrix,
                             rows=rows, cols=cols)
        self.pce_colname = pce_colname
        self.export_colname = export_colname

    # other matrices multplied by FD should also be FD
    def matrix_postmult(self, other):
        other.verify_mult_shape(self)
        matrix = mult_numpy_matrices(other.mat(), self.mat())
        M = FinalDemandMatrix(pce_colname=self.pce_colname,
                              export_colname=self.export_colname,
                              from_matrix=matrix,
                              rows=other.get_rows(),
                              cols=self.get_columns())
        return M

    def get_total(self):
        total = self.mat().sum(1)
        return NamedMatrix(
            square=False,
            rows=self.get_rows(),
            cols=["Final Demand"],
            from_matrix=total)

    def get_pce(self):
        return self.get_named_column(self.pce_colname)

    def get_marginal_pce(self):
        pce = self.get_pce()
        pce.scalar_mult_inplace(1 / pce.sum())
        return pce

    def get_exports(self):
        return self.get_named_column(self.export_colname)

    def get_marginal_export(self):
        exports = self.get_exports()
        exports.scalar_mult_inplace(1 / exports.sum())
        return exports

        



