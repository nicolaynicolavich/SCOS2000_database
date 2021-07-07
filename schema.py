import sys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import CheckConstraint
from sqlalchemy.sql import exists
import functions

Base = declarative_base()

"""Association tables (used for many-to-many relations)"""
PCF_CUR = Table('PCF_CUR_table', Base.metadata,
                Column('PCF_NAME', Integer, ForeignKey('PCF_table.PCF_NAME')),
                Column('CUR_PNAME', Integer, ForeignKey('CUR_table.CUR_PNAME'))
                )

PCF_GRPA = Table('PCF_GRPA_table', Base.metadata,
                 Column('PCF_NAME', Integer, ForeignKey('PCF_table.PCF_NAME')),
                 Column('GRPA_PANAME', Integer, ForeignKey('GRPA_table.GRPA_PANAME'))
                 )

"""Monitoring tables (Figure 1)"""


class CUR(Base):
    __tablename__ = 'CUR_table'
    CUR_PNAME = Column(String(8), CheckConstraint('LENGTH("CUR_PNAME") <= 8'), primary_key=True, nullable=False)
    CUR_POS = Column(Integer, CheckConstraint("CUR_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("CUR_POS") <= 2'),
                     primary_key=True, nullable=False)
    CUR_RLCHK = Column(String(8), CheckConstraint('LENGTH("CUR_RLCHK") <= 8'), nullable=False)
    CUR_VALPAR = Column(Integer, CheckConstraint("CUR_VALPAR < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("CUR_VALPAR") <= 5'), nullable=False)
    # ForeignKey('LGF_table.LGF_IDENT'), ForeignKey('MCF_table.MCF_IDENT'), ForeignKey('CAF_table.CAF_NUMBR')
    CUR_SELECT = Column(String(10), CheckConstraint('LENGTH("CUR_SELECT") <= 10'),
                        nullable=False)

    # LGF_rel= relationship("LGF", use list= False, back_populates= 'CUR_rel')
    PCF_rel = relationship("PCF", secondary=PCF_CUR, back_populates='CUR_rel')

    integer_maxlen = {
        'CUR_POS': 2,
        'CUR_VALPAR': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CUR(
            CUR_PNAME=None,
            CUR_POS=None,
            CUR_RLCHK=None,
            CUR_VALPAR=None,
            CUR_SELECT=None
        )
        return object1


# PCF
class PLF(Base):
    __tablename__ = 'PLF_table'
    PLF_NAME = Column(String(8), CheckConstraint('LENGTH("PLF_NAME") <= 8'), ForeignKey('PCF_table.PCF_NAME'),
                      primary_key=True, nullable=False)
    PLF_SPID = Column(Integer, CheckConstraint("PLF_SPID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PLF_SPID") <= 10'), ForeignKey('PID_table.PID_SPID'), primary_key=True,
                      nullable=False)
    PLF_OFFBY = Column(Integer, CheckConstraint("PLF_OFFBY < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PLF_OFFBY") <= 5'), nullable=False)
    PLF_OFFBI = Column(Integer, CheckConstraint("PLF_OFFBI < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PLF_OFFBI") <= 1'), nullable=False)
    PLF_NBOCC = Column(Integer, CheckConstraint("PLF_NBOCC < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PLF_NBOCC") <= 4'))
    PLF_LGOCC = Column(Integer, CheckConstraint("PLF_LGOCC < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PLF_LGOCC") <= 5'))
    PLF_TIME = Column(Integer, CheckConstraint("PLF_TIME < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PLF_TIME") <= 9'))
    PLF_TDOCC = Column(Integer, CheckConstraint("PLF_TDOCC < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PLF_TDOCC") <= 9'))

    PCF_rel = relationship('PCF', back_populates='PLF_rel')
    PID_rel = relationship('PID', back_populates='PLF_rel')

    integer_maxlen = {
        'PLF_SPID': 10,
        'PLF_OFFBY': 5,
        'PLF_OFFBI': 1,
        'PLF_NBOCC': 4,
        'PLF_LGOCC': 5,
        'PLF_TIME': 9,
        'PLF_TDOCC': 9
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PLF(
            PLF_NAME=None,
            PLF_SPID=None,
            PLF_OFFBY=None,
            PLF_OFFBI=None,
            PLF_NBOCC=None,
            PLF_LGOCC=None,
            PLF_TIME=None,
            PLF_TDOCC=None
        )
        return object1


# VPD
class PID(Base):
    __tablename__ = 'PID_table'
    PID_TYPE = Column(Integer, CheckConstraint("PID_TYPE < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PID_TYPE") <= 3'), primary_key=True, nullable=False)
    PID_STYPE = Column(Integer, CheckConstraint("PID_STYPE < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PID_STYPE") <= 3'), primary_key=True, nullable=False)
    PID_APID = Column(Integer, CheckConstraint("PID_APID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PID_APID") <= 5'), primary_key=True, nullable=False)
    PID_PI1_VAL = Column(Integer, CheckConstraint("PID_PI1_VAL < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PID_PI1_VAL") <= 10'), primary_key=True)
    PID_PI2_VAL = Column(Integer, CheckConstraint("PID_PI2_VAL < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PID_PI2_VAL") <= 10'), primary_key=True)
    PID_SPID = Column(Integer, CheckConstraint("PID_SPID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PID_SPID") <= 10'), primary_key=True, nullable=False)
    PID_DESCR = Column(String(64), CheckConstraint('LENGTH("PID_DESCR") <= 64'))
    PID_UNIT = Column(String(8), CheckConstraint('LENGTH("PID_UNIT") <= 8'))  # field will not be used by SCOS-2000
    PID_TPSD = Column(Integer, CheckConstraint("PID_TPSD < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PID_TPSD") <= 10'))
    PID_DFHSIZE = Column(Integer, CheckConstraint("PID_DFHSIZE < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PID_DFHSIZE") <= 2'), nullable=False)
    PID_TIME = Column(String(1), CheckConstraint('LENGTH("PID_TIME") <= 1'))
    PID_INTER = Column(Integer, CheckConstraint("PID_INTER < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PID_INTER") <= 8'))
    PID_VALID = Column(String(1), CheckConstraint('LENGTH("PID_VALID") <= 1'))
    PID_CHECK = Column(Integer, CheckConstraint("PID_CHECK < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PID_CHECK") <= 1'))
    PID_EVENT = Column(String(1), CheckConstraint('LENGTH("PID_EVENT") <= 1'))
    PID_EVID = Column(String(17), CheckConstraint('LENGTH("PID_EVID") <= 17'))

    GRPK_rel = relationship('GRPK', back_populates='PID_rel', cascade="delete, all")
    PLF_rel = relationship('PLF', back_populates='PID_rel', cascade="delete, all")
    VPD_rel = relationship('VPD', back_populates='PID_rel', cascade="delete, all")
    TPCF_rel = relationship('TPCF', back_populates='PID_rel', cascade="delete, all")

    integer_maxlen = {
        'PID_TYPE': 3,
        'PID_STYPE': 3,
        'PID_APID': 5,
        'PID_PI1_VAL': 10,
        'PID_PI2_VAL': 10,
        'PID_SPID': 10,
        'PID_TPSD': 10,
        'PID_DFHSIZE': 2,
        'PID_INTER': 8,
        'PID_CHECK': 1
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PID(
            PID_TYPE=None,
            PID_STYPE=None,
            PID_APID=None,
            PID_PI1_VAL=None,
            PID_PI2_VAL=None,
            PID_SPID=None,
            PID_DESCR=None,
            PID_UNIT=None,
            PID_TPSD=None,
            PID_DFHSIZE=None,
            PID_TIME=None,
            PID_INTER=None,
            PID_VALID=None,
            PID_CHECK=None,
            PID_EVENT=None,
            PID_EVID=None
        )
        return object1


class TPCF(Base):
    __tablename__ = 'TPCF_table'
    TPCF_SPID = Column(Integer, CheckConstraint("TPCF_SPID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("TPCF_SPID") <= 10'), ForeignKey('PID_table.PID_SPID'), primary_key=True,
                       nullable=False)
    TPCF_NAME = Column(String(12), CheckConstraint('LENGTH("TPCF_NAME") <= 12'))
    TPCF_SIZE = Column(Integer, CheckConstraint("TPCF_SIZE < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("TPCF_SIZE") <= 8'))  # field will not be used by SCOS-2000

    PID_rel = relationship('PID', back_populates='TPCF_rel')

    integer_maxlen = {
        'TPCF_SPID': 10,
        'TPCF_SIZE': 8
    }

    @classmethod
    def createEmptyObject(self):
        object1 = TPCF(
            TPCF_SPID=None,
            TPCF_NAME=None,
            TPCF_SIZE=None
        )
        return object1


class LGF(Base):
    __tablename__ = 'LGF_table'
    LGF_IDENT = Column(String(10), CheckConstraint('LENGTH("LGF_IDENT") <= 10'), primary_key=True, nullable=False)
    LGF_DESCR = Column(String(32), CheckConstraint('LENGTH("LGF_DESCR") <= 32'))
    LGF_POL1 = Column(String(14), CheckConstraint('LENGTH("LGF_POL1") <= 14'), nullable=False)
    LGF_POL2 = Column(String(14), CheckConstraint('LENGTH("LGF_POL2") <= 14'))
    LGF_POL3 = Column(String(14), CheckConstraint('LENGTH("LGF_POL3") <= 14'))
    LGF_POL4 = Column(String(14), CheckConstraint('LENGTH("LGF_POL4") <= 14'))
    LGF_POL5 = Column(String(14), CheckConstraint('LENGTH("LGF_POL5") <= 14'))

    # CUR_rel= relationship("CUR", uselist= False, back_populates= 'LGF_rel')
    # PCF_rel= relationship('PCF', back_populates= 'LGF_rel')

    @classmethod
    def createEmptyObject(self):
        object1 = LGF(
            LGF_IDENT=None,
            LGF_DESCR=None,
            LGF_POL1=None,
            LGF_POL2=None,
            LGF_POL3=None,
            LGF_POL4=None,
            LGF_POL5=None
        )
        return object1


class MCF(Base):
    __tablename__ = 'MCF_table'
    MCF_IDENT = Column(String(10), CheckConstraint('LENGTH("MCF_IDENT") <= 10'), primary_key=True, nullable=False)
    MCF_DESCR = Column(String(32), CheckConstraint('LENGTH("MCF_DESCR") <= 32'))
    MCF_POL1 = Column(String(14), CheckConstraint('LENGTH("MCF_POL1") <= 14'), nullable=False)
    MCF_POL2 = Column(String(14), CheckConstraint('LENGTH("MCF_POL2") <= 14'))
    MCF_POL3 = Column(String(14), CheckConstraint('LENGTH("MCF_POL3") <= 14'))
    MCF_POL4 = Column(String(14), CheckConstraint('LENGTH("MCF_POL4") <= 14'))
    MCF_POL5 = Column(String(14), CheckConstraint('LENGTH("MCF_POL5") <= 14'))

    # CUR_rel= relationship('CUR', uselist= False, back_populates= 'MCF_rel')
    # PCF_rel= relationship('PCF', back_populates= 'MCF_rel')

    @classmethod
    def createEmptyObject(self):
        object1 = MCF(
            MCF_IDENT=None,
            MCF_DESCR=None,
            MCF_POL1=None,
            MCF_POL2=None,
            MCF_POL3=None,
            MCF_POL4=None,
            MCF_POL5=None
        )
        return object1


class CAF(Base):
    __tablename__ = 'CAF_table'
    CAF_NUMBR = Column(String(10), CheckConstraint('LENGTH("CAF_NUMBR") <= 10'), primary_key=True, nullable=False)
    CAF_DESCR = Column(String(32), CheckConstraint('LENGTH("CAF_DESCR") <= 32'))
    CAF_ENGFMT = Column(String(1), CheckConstraint('LENGTH("CAF_ENGFMT") <= 1'), nullable=False)
    CAF_RAWFMT = Column(String(1), CheckConstraint('LENGTH("CAF_RAWFMT") <= 1'), nullable=False)
    CAF_RADIX = Column(String(1), CheckConstraint('LENGTH("CAF_RADIX") <= 1'))
    CAF_UNIT = Column(String(4), CheckConstraint('LENGTH("CAF_UNIT") <= 4'))  # field will not be used by SCOS-2000
    CAF_NCURVE = Column(Integer, CheckConstraint("CAF_NCURVE < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("CAF_NCURVE") <= 3'))  # field will not be used by SCOS-2000
    CAF_INTER = Column(String(1), CheckConstraint('LENGTH("CAF_INTER") <= 1'))

    CAP_rel = relationship("CAP", back_populates="CAF_rel", cascade="delete, all")
    # PCF_rel= relationship("PCF", back_populates= "CAF_rel")

    integer_maxlen = {
        'CAF_NCURVE': 3
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CAF(
            CAF_NUMBR=None,
            CAF_DESCR=None,
            CAF_ENGFMT=None,
            CAF_RAWFMT=None,
            CAF_RADIX=None,
            CAF_UNIT=None,
            CAF_NCURVE=None,
            CAF_INTER=None
        )
        return object1

    def __repr__(self):
        return """
              CAF_NUMBR= %s
              CAF_DESCR= %s
              CAF_ENGFMT= %s
              CAF_RAWFMT= %s
              CAF_RADIX= %s
              CAF_UNIT= %s
              CAF_NCURVE= %s
              CAF_INTER= %s
              """ % (str(self.CAF_NUMBR), str(self.CAF_DESCR), str(self.CAF_ENGFMT), str(self.CAF_RAWFMT),
                                  str(self.CAF_RADIX), str(self.CAF_UNIT), str(self.CAF_NCURVE), str(self.CAF_INTER))


class TXF(Base):
    __tablename__ = 'TXF_table'
    TXF_NUMBR = Column(String(10), CheckConstraint('LENGTH("TXF_NUMBR") <= 10'), primary_key=True, nullable=False)
    TXF_DESCR = Column(String(32), CheckConstraint('LENGTH("TXF_DESCR") <= 32'))
    TXF_RAWFMT = Column(String(1), CheckConstraint('LENGTH("TXF_RAWFMT") <= 1'), nullable=False)
    TXF_NALIAS = Column(Integer, CheckConstraint("TXF_NALIAS < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("TXF_NALIAS") <= 3'))

    TXP_rel = relationship('TXP', back_populates='TXF_rel', cascade="delete, all")
    # PCF_rel= relationship('PCF', back_populates= 'TXF_rel')

    integer_maxlen = {
        'TXF_NALIAS': 3
    }

    @classmethod
    def createEmptyObject(self):
        object1 = TXF(
            TXF_NUMBR=None,
            TXF_DESCR=None,
            TXF_RAWFMT=None,
            TXF_NALIAS=None
        )
        return object1


class OCF(Base):
    __tablename__ = 'OCF_table'
    OCF_NAME = Column(String(8), CheckConstraint('LENGTH("OCF_NAME") <= 8'), ForeignKey('PCF_table.PCF_NAME'),
                      primary_key=True, nullable=False)
    OCF_NBCHCK = Column(Integer, CheckConstraint("OCF_NBCHCK < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("OCF_NBCHCK") <= 2'), nullable=False)
    OCF_NBOOL = Column(Integer, CheckConstraint("OCF_NBOOL < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("OCF_NBOOL") <= 2'), nullable=False)
    OCF_INTER = Column(String(1), CheckConstraint('LENGTH("OCF_INTER") <= 1'), nullable=False)
    OCF_CODIN = Column(String(1), CheckConstraint('LENGTH("OCF_CODIN") <= 1'), nullable=False)

    PCF_rel = relationship('PCF', back_populates='OCF_rel')
    OCP_rel = relationship('OCP', back_populates='OCF_rel', cascade="delete, all")

    integer_maxlen = {
        'OCF_NBCHCK': 2,
        'OCF_NBOOL': 2
    }

    @classmethod
    def createEmptyObject(self):
        object1 = OCF(
            OCF_NAME=None,
            OCF_NBCHCK=None,
            OCF_NBOOL=None,
            OCF_INTER=None,
            OCF_CODIN=None
        )
        return object1


class CAP(Base):
    __tablename__ = 'CAP_table'
    CAP_NUMBR = Column(String(10), CheckConstraint('LENGTH("CAP_NUMBR") <= 10'), ForeignKey('CAF_table.CAF_NUMBR'),
                       nullable=False, primary_key=True)
    CAP_XVALS = Column(String(14), CheckConstraint('LENGTH("CAP_XVALS") <= 14'), nullable=False, primary_key=True)
    CAP_YVALS = Column(String(14), CheckConstraint('LENGTH("CAP_YVALS") <= 14'), nullable=False)

    CAF_rel = relationship("CAF", back_populates="CAP_rel")

    @classmethod
    def createEmptyObject(self):
        object1 = CAP(
            CAP_NUMBR=None,
            CAP_XVALS=None,
            CAP_YVALS=None
        )
        return object1


class TXP(Base):
    __tablename__ = 'TXP_table'
    TXP_NUMBR = Column(String(10), CheckConstraint('LENGTH("TXP_NUMBR") <= 10'), ForeignKey('TXF_table.TXF_NUMBR'),
                       nullable=False, primary_key=True)
    TXP_FROM = Column(String(14), CheckConstraint('LENGTH("TXP_FROM") <= 14'), nullable=False, primary_key=True)
    TXP_TO = Column(String(14), CheckConstraint('LENGTH("TXP_TO") <= 14'), nullable=False)
    TXP_ALTXT = Column(String(14), CheckConstraint('LENGTH("TXP_ALTXT") <= 14'), nullable=False)

    TXF_rel = relationship('TXF', back_populates='TXP_rel')

    @classmethod
    def createEmptyObject(self):
        object1 = TXP(
            TXP_NUMBR=None,
            TXP_FROM=None,
            TXP_TO=None,
            TXP_ALTXT=None
        )
        return object1


class OCP(Base):
    __tablename__ = 'OCP_table'
    OCP_NAME = Column(String(8), CheckConstraint('LENGTH("OCP_NAME") <= 8'), ForeignKey('OCF_table.OCF_NAME'),
                      nullable=False, primary_key=True)
    OCP_POS = Column(Integer, CheckConstraint("OCP_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("OCP_POS") <= 2'),
                     nullable=False, primary_key=True)  # field will not be used by SCOS-2000
    OCP_TYPE = Column(String(1), CheckConstraint('LENGTH("OCP_TYPE") <= 1'), nullable=False)
    OCP_LVALU = Column(String(14), CheckConstraint('LENGTH("OCP_LVALU") <= 14'))
    OCP_HVALU = Column(String(14), CheckConstraint('LENGTH("OCP_HVALU") <= 14'))
    OCP_RLCHK = Column(String(8), CheckConstraint('LENGTH("OCP_RLCHK") <= 8'))
    OCP_VALPAR = Column(Integer, CheckConstraint("OCP_VALPAR < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("OCP_VALPAR") <= 5'))

    OCF_rel = relationship('OCF', back_populates='OCP_rel')

    integer_maxlen = {
        'OCP_POS': 2,
        'OCP_VALPAR': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = OCP(
            OCP_NAME=None,
            OCP_POS=None,
            OCP_TYPE=None,
            OCP_LVALU=None,
            OCP_HVALU=None,
            OCP_RLCHK=None,
            OCP_VALPAR=None
        )
        return object1


class GRPA(Base):
    __tablename__ = 'GRPA_table'
    GRPA_GNAME = Column(String(14), CheckConstraint('LENGTH("GRPA_GNAME") <= 14'), ForeignKey('GRP_table.GRP_NAME'),
                        primary_key=True, nullable=False)
    GRPA_PANAME = Column(String(8), CheckConstraint('LENGTH("GRPA_PANAME") <= 8'), primary_key=True, nullable=False)

    PCF_rel = relationship('PCF', secondary=PCF_GRPA, back_populates='GRPA_rel')
    GRP_rel = relationship('GRP', back_populates='GRPA_rel')

    @classmethod
    def createEmptyObject(self):
        object1 = GRPA(
            GRPA_GNAME=None,
            GRPA_PANAME=None
        )
        return object1


class GRPK(Base):
    __tablename__ = 'GRPK_table'
    GRPK_GNAME = Column(String(14), CheckConstraint('LENGTH("GRPK_GNAME") <= 14'), ForeignKey('GRP_table.GRP_NAME'),
                        primary_key=True, nullable=False)
    GRPK_PKSPID = Column(Integer, CheckConstraint("GRPK_PKSPID < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("GRPK_PKSPID") <= 10'), ForeignKey("PID_table.PID_SPID"),
                         primary_key=True, nullable=False)

    GRP_rel = relationship('GRP', back_populates='GRPK_rel')
    PID_rel = relationship('PID', back_populates='GRPK_rel')

    integer_maxlen = {
        'GRPK_PKSPID': 10
    }

    @classmethod
    def createEmptyObject(self):
        object1 = GRPK(
            GRPK_GNAME=None,
            GRPK_PKSPID=None
        )
        return object1


class GRP(Base):
    __tablename__ = 'GRP_table'
    GRP_NAME = Column(String(14), CheckConstraint('LENGTH("GRP_NAME") <= 14'), nullable=False, primary_key=True)
    GRP_DESCR = Column(String(24), CheckConstraint('LENGTH("GRP_DESCR") <= 24'), nullable=False)
    GRP_GTYPE = Column(String(2), CheckConstraint('LENGTH("GRP_GTYPE") <= 2'), nullable=False)

    GRPA_rel = relationship('GRPA', back_populates='GRP_rel', cascade="delete, all")
    GRPK_rel = relationship('GRPK', back_populates='GRP_rel', cascade="delete, all")

    @classmethod
    def createEmptyObject(self):
        object1 = GRP(
            GRP_NAME=None,
            GRP_DESCR=None,
            GRP_GTYPE=None
        )
        return object1


"""Display tables (Figure 2)"""


class PCF(Base):
    __tablename__ = 'PCF_table'
    PCF_NAME = Column(String(8), CheckConstraint('LENGTH("PCF_NAME") <= 8'), primary_key=True, nullable=False)
    PCF_DESCR = Column(String(24), CheckConstraint('LENGTH("PCF_DESCR") <= 24'))
    PCF_PID = Column(Integer, CheckConstraint("PCF_PID < %d" % sys.maxsize), CheckConstraint('LENGTH("PCF_PID") <= 10'))
    PCF_UNIT = Column(String(4), CheckConstraint('LENGTH("PCF_UNIT") <= 4'))
    PCF_PTC = Column(Integer, CheckConstraint("PCF_PTC < %d" % sys.maxsize), CheckConstraint('LENGTH("PCF_PTC") <= 2'),
                     nullable=False)
    PCF_PFC = Column(Integer, CheckConstraint("PCF_PFC < %d" % sys.maxsize), CheckConstraint('LENGTH("PCF_PFC") <= 5'),
                     nullable=False)
    PCF_WIDTH = Column(Integer, CheckConstraint("PCF_WIDTH < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PCF_WIDTH") <= 6'))
    PCF_VALID = Column(String(8), CheckConstraint('LENGTH("PCF_VALID") <= 8'), ForeignKey('PCF_table.PCF_NAME'))
    PCF_RELATED = Column(String(8), CheckConstraint('LENGTH("PCF_RELATED") <= 8'), ForeignKey('PCF_table.PCF_NAME'))
    PCF_CATEG = Column(String(1), CheckConstraint('LENGTH("PCF_CATEG") <= 1'), nullable=False)
    PCF_NATUR = Column(String(1), CheckConstraint('LENGTH("PCF_NATUR") <= 1'), nullable=False)

    # ForeignKey('TXF_table.TXF_NUMBR'), ForeignKey('CAF_table.CAF_NUMBR'),
    # ForeignKey('MCF_table.MCF_NUMBR'), ForeignKey('LGF_table.LGF_NUMBR')
    PCF_CURTX = Column(String(8), CheckConstraint('LENGTH("PCF_CURTX") <= 8'))

    # field will not be used by SCOS-2000
    PCF_INTER = Column(String(1), CheckConstraint('LENGTH("PCF_INTER") <= 1'))
    PCF_USCON = Column(String(1), CheckConstraint('LENGTH("PCF_USCON") <= 1'))
    PCF_DECIM = Column(Integer, CheckConstraint("PCF_DECIM < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PCF_DECIM") <= 3'))
    PCF_PARVAL = Column(String(14), CheckConstraint('LENGTH("PCF_PARVAL") <= 14'))

    # field will not be used by SCOS-2000
    PCF_SUBSYS = Column(String(8), CheckConstraint('LENGTH("PCF_SUBSYS") <= 8'))
    PCF_VALPAR = Column(Integer, CheckConstraint("PCF_VALPAR < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("PCF_VALPAR") <= 5'))

    # field will not be used by SCOS-2000
    PCF_SPTYPE = Column(String(1), CheckConstraint('LENGTH("PCF_SPTYPE") <= 1'))
    PCF_CORR = Column(String(1), CheckConstraint('LENGTH("PCF_CORR") <= 1'))
    PCF_OBTID = Column(Integer, CheckConstraint("PCF_OBTID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PCF_OBTID") <= 5'))
    PCF_DARC = Column(String(1), CheckConstraint('LENGTH("PCF_DARC") <= 1'))
    PCF_ENDIAN = Column(String(1), CheckConstraint('LENGTH("PCF_ENDIAN") <= 1'))

    DPC_rel = relationship("DPC", back_populates="PCF_rel", cascade="delete, all")
    GPC_rel = relationship("GPC", back_populates="PCF_rel")
    SPC_rel = relationship("SPC", back_populates="PCF_rel", cascade="delete, all")
    VPD_rel = relationship("VPD", back_populates="PCF_rel", cascade="delete, all")
    CUR_rel = relationship("CUR", secondary=PCF_CUR, back_populates="PCF_rel")
    PLF_rel = relationship("PLF", back_populates="PCF_rel", cascade="delete, all")
    OCF_rel = relationship("OCF", uselist=False, back_populates="PCF_rel", cascade="delete, all")
    GRPA_rel = relationship("GRPA", secondary=PCF_GRPA, back_populates="PCF_rel")
    # TXF_rel= relationship("TXF", back_populates= "PCF_rel")
    # CAF_rel= relationship("CAF", back_populates= "PCF_rel")
    # MCF_rel= relationship("MCF", back_populates= "PCF_rel")
    # LGF_rel= relationship("LGF", back_populates= "PCF_rel")

    integer_maxlen = {
        'PCF_PID': 10,
        'PCF_PTC': 2,
        'PCF_PFC': 5,
        'PCF_WIDTH': 6,
        'PCF_DECIM': 3,
        'PCF_VALPAR': 5,
        'PCF_OBTID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PCF(
            PCF_NAME=None,
            PCF_DESCR=None,
            PCF_PID=None,
            PCF_UNIT=None,
            PCF_PTC=None,
            PCF_PFC=None,
            PCF_WIDTH=None,
            PCF_VALID=None,
            PCF_RELATED=None,
            PCF_CATEG=None,
            PCF_NATUR=None,
            PCF_CURTX=None,
            PCF_INTER=None,
            PCF_USCON=None,
            PCF_DECIM=None,
            PCF_PARVAL=None,
            PCF_SUBSYS=None,
            PCF_VALPAR=None,
            PCF_SPTYPE=None,
            PCF_CORR=None,
            PCF_OBTID=None,
            PCF_DARC=None,
            PCF_ENDIAN=None,
        )
        return object1


class DPC(Base):
    __tablename__ = 'DPC_table'
    DPC_NUMBE = Column(String(8), CheckConstraint('LENGTH("DPC_NUMBE") <= 8'), ForeignKey('DPF_table.DPF_NUMBE'),
                       primary_key=True, nullable=False)
    DPC_NAME = Column(String(8), CheckConstraint('LENGTH("DPC_NAME") <= 8'), ForeignKey('PCF_table.PCF_NAME'))
    DPC_FLDN = Column(Integer, CheckConstraint("DPC_FLDN < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("DPC_FLDN") <= 2'), primary_key=True, nullable=False)
    DPC_COMM = Column(Integer, CheckConstraint("DPC_COMM < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("DPC_COMM") <= 4'))
    DPC_MODE = Column(String(1), CheckConstraint('LENGTH("DPC_MODE") <= 1'))
    DPC_FORM = Column(String(1), CheckConstraint('LENGTH("DPC_FORM") <= 1'))
    DPC_TEXT = Column(String(32), CheckConstraint('LENGTH("DPC_TEXT") <= 32'))

    DPF_rel = relationship("DPF", back_populates="DPC_rel")
    PCF_rel = relationship("PCF", back_populates="DPC_rel")

    integer_maxlen = {
        'DPC_FLDN': 2,
        'DPC_COMM': 4
    }

    def __repr__(self):
        return """
            DPC_NUMBE = %s
            DPC_NAME = %s
            DPC_FLDN = %s
            DPC_COMM = %s
            DPC_MODE = %s
            DPC_FORM = %s
            DPC_TEXT = %s
            """ % (str(self.DPC_NUMBE), str(self.DPC_NAME), str(self.DPC_FLDN),
                   str(self.DPC_COMM), str(self.DPC_MODE),
                   str(self.DPC_FORM), str(self.DPC_TEXT))

    @classmethod
    def createEmptyObject(self):
        object1 = DPC(
            DPC_NUMBE=None,
            DPC_NAME=None,
            DPC_FLDN=None,
            DPC_COMM=None,
            DPC_MODE=None,
            DPC_FORM=None,
            DPC_TEXT=None
        )
        return object1


class GPC(Base):
    __tablename__ = 'GPC_table'
    GPC_NUMBE = Column(String(8), CheckConstraint('LENGTH("GPC_NUMBE") <= 8'), ForeignKey('GPF_table.GPF_NUMBE'),
                       primary_key=True, nullable=False)
    GPC_POS = Column(Integer, CheckConstraint("GPC_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("GPC_POS") <= 1'),
                     primary_key=True, nullable=False)  # field will not be used by SCOS-2000
    GPC_WHERE = Column(String(1), CheckConstraint('LENGTH("GPC_WHERE") <= 1'), nullable=False)
    GPC_NAME = Column(String(8), CheckConstraint('LENGTH("GPC_NAME") <= 8'), ForeignKey('PCF_table.PCF_NAME'),
                      nullable=False)
    GPC_RAW = Column(String(1), CheckConstraint('LENGTH("GPC_RAW") <= 1'))
    GPC_MINIM = Column(String(14), CheckConstraint('LENGTH("GPC_MINIM") <= 14'), nullable=False)
    GPC_MAXIM = Column(String(14, CheckConstraint('LENGTH("GPC_MAXIM") <= 14')), nullable=False)
    GPC_PRCLR = Column(String(1), CheckConstraint('LENGTH("GPC_PRCLR") <= 1'), nullable=False)
    GPC_SYMB0 = Column(String(1, CheckConstraint('LENGTH("GPC_SYMB0") <= 1')))
    GPC_LINE = Column(String(1), CheckConstraint('LENGTH("GPC_LINE") <= 1'))
    GPC_DOMAIN = Column(Integer, CheckConstraint("GPC_DOMAIN < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("GPC_DOMAIN") <= 5'))

    GPF_rel = relationship("GPF", back_populates="GPC_rel")
    PCF_rel = relationship("PCF", back_populates="GPC_rel", cascade="delete, all")

    integer_maxlen = {
        'GPC_POS': 1,
        'GPC_DOMAIN': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = GPC(
            GPC_NUMBE=None,
            GPC_POS=None,
            GPC_WHERE=None,
            GPC_NAME=None,
            GPC_RAW=None,
            GPC_MINIM=None,
            GPC_MAXIM=None,
            GPC_PRCLR=None,
            GPC_SYMB0=None,
            GPC_LINE=None,
            GPC_DOMAIN=None
        )
        return object1


class SPC(Base):
    __tablename__ = 'SPC_table'
    SPC_NUMBE = Column(String(8), CheckConstraint('LENGTH("SPC_NUMBE") <= 8'), ForeignKey("SPF_table.SPF_NUMBE"),
                       primary_key=True, nullable=False)
    SPC_POS = Column(Integer, CheckConstraint("SPC_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("SPC_POS") <= 1'),
                     primary_key=True, nullable=False)  # field will not be used by SCOS-2000
    SPC_NAME = Column(String(8), CheckConstraint('LENGTH("SPC_NAME") <= 8'), ForeignKey('PCF_table.PCF_NAME'),
                      nullable=False)
    SPC_UPDT = Column(String(1), CheckConstraint('LENGTH("SPC_UPDT") <= 1'))
    SPC_MODE = Column(String(1), CheckConstraint('LENGTH("SPC_MODE") <= 1'))
    SPC_FORM = Column(String(1, CheckConstraint('LENGTH("SPC_FORM") <= 1')))
    SPC_BACK = Column(String(1), CheckConstraint('LENGTH("SPC_BACK") <= 1'))
    SPC_FORE = Column(String(1), CheckConstraint('LENGTH("SPC_FORE") <= 1'), nullable=False)

    SPF_rel = relationship("SPF", back_populates="SPC_rel")
    PCF_rel = relationship("PCF", back_populates="SPC_rel")

    integer_maxlen = {
        'SPC_POS': 1
    }

    @classmethod
    def createEmptyObject(self):
        object1 = SPC(
            SPC_NUMBE=None,
            SPC_POS=None,
            SPC_NAME=None,
            SPC_UPDT=None,
            SPC_MODE=None,
            SPC_FORM=None,
            SPC_BACK=None,
            SPC_FORE=None
        )
        return object1


class VPD(Base):
    __tablename__ = 'VPD_table'
    VPD_TPSD = Column(Integer, CheckConstraint("VPD_TPSD < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("VPD_TPSD") <= 10'), ForeignKey('PID_table.PID_TPSD'), primary_key=True,
                      nullable=False)
    VPD_POS = Column(Integer, CheckConstraint("VPD_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("VPD_POS") <= 4'),
                     primary_key=True, nullable=False)  # field will not be used by SCOS-2000
    VPD_NAME = Column(String(8), CheckConstraint('LENGTH("VPD_NAME") <= 8'), ForeignKey('PCF_table.PCF_NAME'),
                      nullable=False)
    VPD_GRPSIZE = Column(Integer, CheckConstraint("VPD_GRPSIZE < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("VPD_GRPSIZE") <= 3'))
    VPD_FIXREP = Column(Integer, CheckConstraint("VPD_FIXREP < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("VPD_FIXREP") <= 3'))
    VPD_CHOICE = Column(String(1), CheckConstraint('LENGTH("VPD_CHOICE") <= 1'))
    VPD_PIDREF = Column(String(1, CheckConstraint('LENGTH("VPD_PIDREF") <= 1')))
    VPD_DISDESC = Column(String(16), CheckConstraint('LENGTH("VPD_DISDESC") <= 16'))
    VPD_WIDTH = Column(Integer, CheckConstraint("VPD_WIDTH < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("VPD_WIDTH") <= 2'), nullable=False)
    VPD_JUSTIFY = Column(String(1), CheckConstraint('LENGTH("VPD_JUSTIFY") <= 1'))
    VPD_NEWLINE = Column(String(1), CheckConstraint('LENGTH("VPD_NEWLINE") <= 1'))
    VPD_DCHAR = Column(Integer, CheckConstraint("VPD_DCHAR < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("VPD_DCHAR") <= 1'))
    VPD_FORM = Column(String(1), CheckConstraint('LENGTH("VPD_FORM") <= 1'))
    VPD_OFFSET = Column(Integer, CheckConstraint("VPD_OFFSET < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("VPD_OFFSET") <= 6'))

    PCF_rel = relationship("PCF", back_populates="VPD_rel")
    PID_rel = relationship("PID", back_populates="VPD_rel")

    integer_maxlen = {
        'VPD_TPSD': 10,
        'VPD_POS': 4,
        'VPD_GRPSIZE': 3,
        'VPD_FIXREP': 3,
        'VPD_WIDTH': 2,
        'VPD_DCHAR': 1,
        'VPD_OFFSET': 6
    }

    @classmethod
    def createEmptyObject(self):
        object1 = VPD(
            VPD_TPSD=None,
            VPD_POS=None,
            VPD_NAME=None,
            VPD_GRPSIZE=None,
            VPD_FIXREP=None,
            VPD_CHOICE=None,
            VPD_PIDREF=None,
            VPD_DISDESC=None,
            VPD_WIDTH=None,
            VPD_JUSTIFY=None,
            VPD_NEWLINE=None,
            VPD_DCHAR=None,
            VPD_FORM=None,
            VPD_OFFSET=None
        )
        return object1


class DPF(Base):
    __tablename__ = 'DPF_table'
    DPF_NUMBE = Column(String(8), CheckConstraint('LENGTH("DPF_NUMBE") <= 8'), primary_key=True, nullable=False)
    DPF_TYPE = Column(String(1), CheckConstraint('LENGTH("DPF_TYPE") <= 1'), nullable=False)
    DPF_HEAD = Column(String(32), CheckConstraint('LENGTH("DPF_HEAD") <= 32'))

    DPC_rel = relationship("DPC", back_populates="DPF_rel", cascade="delete, all")

    def __repr__(self):
        return """
            DPF_NUMBE = %s
            DPF_TYPE = %s
            DPF_HEAD = %s
            """ % (self.DPF_NUMBE, self.DPF_TYPE, self.DPF_HEAD)

    @classmethod
    def createEmptyObject(self):
        object1 = DPF(
            DPF_NUMBE=None,
            DPF_TYPE=None,
            DPF_HEAD=None
        )
        return object1


class GPF(Base):
    __tablename__ = 'GPF_table'
    GPF_NUMBE = Column(String(8), CheckConstraint('LENGTH("GPF_NUMBE") <= 8'), primary_key=True, nullable=False)
    GPF_TYPE = Column(String(1), CheckConstraint('LENGTH("GPF_TYPE") <= 1'), nullable=False)
    GPF_HEAD = Column(String(32), CheckConstraint('LENGTH("GPF_HEAD") <= 32'))
    GPF_SCROL = Column(String(1), CheckConstraint('LENGTH("GPF_SCROL") <= 1'))
    GPF_HCOPY = Column(String(1), CheckConstraint('LENGTH("GPF_HCOPY") <= 1'))
    GPF_DAYS = Column(Integer, CheckConstraint("GPF_DAYS < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("GPF_DAYS") <= 2'), nullable=False)
    GPF_HOURS = Column(Integer, CheckConstraint("GPF_HOURS < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("GPF_HOURS") <= 2'), nullable=False)
    GPF_MINUT = Column(Integer, CheckConstraint("GPF_MINUT < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("GPF_MINUT") <= 2'), nullable=False)
    GPF_AXCLR = Column(String(1), CheckConstraint('LENGTH("GPF_AXCLR") <= 1'), nullable=False)
    GPF_XTICK = Column(Integer, CheckConstraint("GPF_XTICK < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("GPF_XTICK") <= 2'), nullable=False)
    GPF_YTICK = Column(Integer, CheckConstraint("GPF_YTICK < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("GPF_YTICK") <= 2'), nullable=False)
    GPF_XGRID = Column(Integer, CheckConstraint("GPF_XGRID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("GPF_XGRID") <= 2'), nullable=False)
    GPF_YGRID = Column(Integer, CheckConstraint("GPF_YGRID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("GPF_YGRID") <= 2'), nullable=False)
    GPF_UPUN = Column(Integer, CheckConstraint("GPF_UPUN < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("GPF_UPUN") <= 2'))  # field will not be used by SCOS-2000

    GPC_rel = relationship("GPC", back_populates="GPF_rel", cascade="delete, all")

    integer_maxlen = {
        'GPF_DAYS': 2,
        'GPF_HOURS': 2,
        'GPF_MINUT': 2,
        'GPF_XTICK': 2,
        'GPF_YTICK': 2,
        'GPF_XGRID': 2,
        'GPF_YGRID': 2,
        'GPF_UPUN': 2
    }

    @classmethod
    def createEmptyObject(self):
        object1 = GPF(
            GPF_NUMBE=None,
            GPF_TYPE=None,
            GPF_HEAD=None,
            GPF_SCROL=None,
            GPF_HCOPY=None,
            GPF_DAYS=None,
            GPF_HOURS=None,
            GPF_MINUT=None,
            GPF_AXCLR=None,
            GPF_XTICK=None,
            GPF_YTICK=None,
            GPF_XGRID=None,
            GPF_YGRID=None,
            GPF_UPUN=None
        )
        return object1


class SPF(Base):
    __tablename__ = 'SPF_table'
    SPF_NUMBE = Column(String(8), CheckConstraint('LENGTH("SPF_NUMBE") <= 8'), primary_key=True, nullable=False)
    SPF_HEAD = Column(String(32), CheckConstraint('LENGTH("SPF_HEAD") <= 32'))
    SPF_NPAR = Column(Integer, CheckConstraint("SPF_NPAR < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("SPF_NPAR") <= 1'), nullable=False)
    SPF_UPUN = Column(Integer, CheckConstraint("SPF_UPUN < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("SPF_UPUN") <= 2'))  # field will not be used by SCOS-2000

    SPC_rel = relationship("SPC", back_populates="SPF_rel", cascade="delete, all")

    integer_maxlen = {
        'SPF_NPAR': 1,
        'SPF_UPUN': 2
    }

    @classmethod
    def createEmptyObject(self):
        object1 = SPF(
            SPF_NUMBE=None,
            SPF_HEAD=None,
            SPF_NPAR=None,
            SPF_UPUN=None
        )
        return object1


"""Command tables (Figure 3)"""


# PSV
class PTV(Base):
    __tablename__ = 'PTV_table'
    PTV_CNAME = Column(String(8), CheckConstraint('LENGTH("PTV_CNAME") <= 8'), ForeignKey('CCF_table.CCF_CNAME'),
                       primary_key=True, nullable=False)
    PTV_PARNAM = Column(String(8), CheckConstraint('LENGTH("PTV_PARNAM") <= 8'), primary_key=True, nullable=False)
    PTV_INTER = Column(String(1), CheckConstraint('LENGTH("PTV_INTER") <= 1'))
    PTV_VAL = Column(String(17), CheckConstraint('LENGTH("PTV_VAL") <= 17'), nullable=False)

    CCF_rel = relationship("CCF", back_populates="PTV_rel")

    @classmethod
    def createEmptyObject(self):
        object1 = PTV(
            PTV_CNAME=None,
            PTV_PARNAM=None,
            PTV_INTER=None,
            PTV_VAL=None
        )
        return object1


# CSS
# PSM
# CCF

class TCP(Base):
    __tablename__ = 'TCP_table'
    TCP_ID = Column(String(8), CheckConstraint('LENGTH("TCP_ID") <= 8'), primary_key=True, nullable=False)
    TCP_DESC = Column(String(24), CheckConstraint('LENGTH("TCP_DESC") <= 24'))

    PCDF_rel = relationship('PCDF', back_populates='TCP_rel', cascade="delete, all")
    CCF_rel = relationship('CCF', back_populates='TCP_rel', cascade="delete, all")

    @classmethod
    def createEmptyObject(self):
        object1 = TCP(
            TCP_ID=None,
            TCP_DESC=None
        )
        return object1


class PCDF(Base):
    __tablename__ = 'PCDF_table'
    PCDF_TCNAME = Column(String(8), CheckConstraint('LENGTH("PCDF_TCNAME") <= 8'), ForeignKey("TCP_table.TCP_ID"),
                         primary_key=True, nullable=False)
    PCDF_DESC = Column(String(24), CheckConstraint('LENGTH("PCDF_DESC") <= 24'))
    PCDF_TYPE = Column(String(1), CheckConstraint('LENGTH("PCDF_TYPE") <= 1'), nullable=False)
    PCDF_LEN = Column(Integer, CheckConstraint("PCDF_LEN < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PCDF_LEN") <= 4'), nullable=False)
    PCDF_BIT = Column(Integer, CheckConstraint("PCDF_BIT < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PCDF_BIT") <= 4'), primary_key=True, nullable=False)
    PCDF_PNAME = Column(String(8), CheckConstraint('LENGTH("PCDF_PNAME") <= 8'), ForeignKey("PCPC_table.PCPC_PNAME"))
    PCDF_VALUE = Column(String(10), CheckConstraint('LENGTH("PCDF_VALUE") <= 10'), nullable=False)
    PCDF_RADIX = Column(String(1), CheckConstraint('LENGTH("PCDF_RADIX") <= 1'))

    PCPC_rel = relationship("PCPC", back_populates='PCDF_rel')
    TCP_rel = relationship("TCP", back_populates='PCDF_rel')

    integer_maxlen = {
        'PCDF_LEN': 4,
        'PCDF_BIT': 4
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PCDF(
            PCDF_TCNAME=None,
            PCDF_DESC=None,
            PCDF_TYPE=None,
            PCDF_LEN=None,
            PCDF_BIT=None,
            PCDF_PNAME=None,
            PCDF_VALUE=None,
            PCDF_RADIX=None
        )
        return object1


class PCPC(Base):
    __tablename__ = 'PCPC_table'
    PCPC_PNAME = Column(String(8), CheckConstraint('LENGTH("PCPC_PNAME") <= 8'), primary_key=True, nullable=False)
    PCPC_DESC = Column(String(24), CheckConstraint('LENGTH("PCPC_DESC") <= 24'), nullable=False)
    PCPC_CODE = Column(String(1), CheckConstraint('LENGTH("PCPC_CODE") <= 1'))

    PCDF_rel = relationship("PCDF", back_populates='PCPC_rel', cascade="delete, all")

    @classmethod
    def createEmptyObject(self):
        object1 = PCPC(
            PCPC_PNAME=None,
            PCPC_DESC=None,
            PCPC_CODE=None
        )
        return object1


# CDF
# CPC

class CVP(Base):
    __tablename__ = 'CVP_table'
    CVP_TASK = Column(String(8), CheckConstraint('LENGTH("CVP_TASK") <= 8'), ForeignKey('CCF_table.CCF_CNAME'),
                      primary_key=True, nullable=False)
    CVP_TYPE = Column(String(1), CheckConstraint('LENGTH("CVP_TYPE") <= 1'), primary_key=True)
    CVP_CVSID = Column(Integer, CheckConstraint("CVP_CVSID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CVP_CVSID") <= 5'), ForeignKey('CVS_table.CVS_ID'), primary_key=True,
                       nullable=False)

    CVS_rel = relationship('CVS', back_populates='CVP_rel')
    CCF_rel = relationship('CCF', back_populates='CVP_rel')

    integer_maxlen = {
        'CVP_CVSID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CVP(
            CVP_TASK=None,
            CVP_TYPE=None,
            CVP_CVSID=None
        )
        return object1


class CVS(Base):
    __tablename__ = 'CVS_table'
    CVS_ID = Column(Integer, CheckConstraint("CVS_ID < %d" % sys.maxsize), CheckConstraint('LENGTH("CVS_ID") <= 5'),
                    primary_key=True, nullable=False)
    CVS_TYPE = Column(String(1), CheckConstraint('LENGTH("CVS_TYPE") <= 1'), nullable=False)
    CVS_SOURCE = Column(String(1), CheckConstraint('LENGTH("CVS_SOURCE") <= 1'), nullable=False)
    CVS_START = Column(Integer, CheckConstraint("CVS_START < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CVS_START") <= 5'), nullable=False)
    CVS_INTERVAL = Column(Integer, CheckConstraint("CVS_INTERVAL < %d" % sys.maxsize),
                          CheckConstraint('LENGTH("CVS_INTERVAL") <= 5'), nullable=False)
    CVS_SPID = Column(Integer, CheckConstraint("CVS_SPID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("CVS_SPID") <= 10'))  # field will not be used by SCOS-2000
    CVS_UNCERTAINTY = Column(Integer, CheckConstraint("CVS_UNCERTAINTY < %d" % sys.maxsize),
                             CheckConstraint('LENGTH("CVS_UNCERTAINTY") <= 10'))

    CVE_rel = relationship('CVE', back_populates='CVS_rel', cascade="delete, all")
    CVP_rel = relationship('CVP', back_populates='CVS_rel', cascade="delete, all")

    integer_maxlen = {
        'CVS_ID': 5,
        'CVS_START': 5,
        'CVS_INTERVAL': 5,
        'CVS_SPID': 10,
        'CVS_UNCERTAINTY': 10
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CVS(
            CVS_ID=None,
            CVS_TYPE=None,
            CVS_SOURCE=None,
            CVS_START=None,
            CVS_INTERVAL=None,
            CVS_SPID=None,
            CVS_UNCERTAINTY=None
        )
        return object1


class CVE(Base):
    __tablename__ = 'CVE_table'
    CVE_CVSID = Column(Integer, CheckConstraint("CVE_CVSID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CVE_CVSID") <= 5'), ForeignKey('CVS_table.CVS_ID'), primary_key=True,
                       nullable=False)
    CVE_PARNAM = Column(String(8), CheckConstraint('LENGTH("CVE_PARNAM") <= 8'), primary_key=True, nullable=False)
    CVE_INTER = Column(String(8), CheckConstraint('LENGTH("CVE_INTER") <= 8'), nullable=False)
    CVE_VAL = Column(String(17), CheckConstraint('LENGTH("CVE_VAL") <= 17'))
    CVE_TOL = Column(String(17), CheckConstraint('LENGTH("CVE_TOL") <= 17'))
    CVE_CHECK = Column(String(1), CheckConstraint('LENGTH("CVE_CHECK") <= 1'))

    CVS_rel = relationship('CVS', back_populates='CVE_rel')

    integer_maxlen = {
        'CVE_CVSID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CVE(
            CVE_CVSID=None,
            CVE_PARNAM=None,
            CVE_INTER=None,
            CVE_VAL=None,
            CVE_TOL=None,
            CVE_CHECK=None
        )
        return object1


"""Command Sequence tables (Figure 4)"""


# PSV
# PSM
# CSF
# CSP
# CCF
class CSS(Base):
    __tablename__ = 'CSS_table'
    CSS_SQNAME = Column(String(8), CheckConstraint('LENGTH("CSS_SQNAME") <= 8'), ForeignKey("CSF_table.CSF_NAME"),
                        primary_key=True, nullable=False)
    CSS_COMM = Column(String(32), CheckConstraint('LENGTH("CSS_COMM") <= 32'))
    CSS_ENTRY = Column(Integer, CheckConstraint("CSS_ENTRY < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CSS_ENTRY") <= 5'), primary_key=True, nullable=False)
    CSS_TYPE = Column(String(1), CheckConstraint('LENGTH("CSS_TYPE") <= 1'), nullable=False)
    CSS_ELEMID = Column(String(8), CheckConstraint(
        'LENGTH("CSS_ELEMID") <= 8'))  # ForeignKey("CCF_table.CCF_CNAME"), ForeignKey("CSF_table.CSF_NAME")
    CSS_NPARS = Column(Integer, CheckConstraint("CSS_NPARS < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CSS_NPARS") <= 3'))  # field will not be used by SCOS-2000
    CSS_MANDISP = Column(String(1), CheckConstraint('LENGTH("CSS_MANDISP") <= 1'))
    CSS_RELTYPE = Column(String(1), CheckConstraint('LENGTH("CSS_RELTYPE") <= 1'))
    CSS_RELTIME = Column(String(8), CheckConstraint('LENGTH("CSS_RELTIME") <= 8'))
    CSS_EXTIME = Column(String(17), CheckConstraint('LENGTH("CSS_EXTIME") <= 17'))
    CSS_PREVREL = Column(String(1), CheckConstraint('LENGTH("CSS_PREVREL") <= 1'))
    CSS_GROUP = Column(String(1), CheckConstraint('LENGTH("CSS_GROUP") <= 1'))
    CSS_BLOCK = Column(String(1), CheckConstraint('LENGTH("CSS_BLOCK") <= 1'))
    CSS_ILSCOPE = Column(String(1), CheckConstraint('LENGTH("CSS_ILSCOPE") <= 1'))
    CSS_ILSTAGE = Column(String(1), CheckConstraint('LENGTH("CSS_ILSTAGE") <= 1'))
    CSS_DYNPTV = Column(String(1), CheckConstraint('LENGTH("CSS_DYNPTV") <= 1'))
    CSS_STAPTV = Column(String(1), CheckConstraint('LENGTH("CSS_DYNPTV") <= 1'))
    CSS_CEV = Column(String(1), CheckConstraint('LENGTH("CSS_CEV") <= 1'))

    # CCF_rel= relationship('CCF', back_populates= 'CSS_rel')
    CSF_rel = relationship('CSF', back_populates='CSS_rel')

    integer_maxlen = {
        'CSS_ENTRY': 5,
        'CSS_NPARS': 3
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CSS(
            CSS_SQNAME=None,
            CSS_COMM=None,
            CSS_ENTRY=None,
            CSS_TYPE=None,
            CSS_ELEMID=None,
            CSS_NPARS=None,
            CSS_MANDISP=None,
            CSS_RELTYPE=None,
            CSS_RELTIME=None,
            CSS_EXTIME=None,
            CSS_PREVREL=None,
            CSS_GROUP=None,
            CSS_BLOCK=None,
            CSS_ILSCOPE=None,
            CSS_ILSTAGE=None,
            CSS_DYNPTV=None,
            CSS_CEV=None
        )
        return object1


# CDF
# SDF

"""Parameter set tables (Figure 5)"""


class CCF(Base):
    __tablename__ = 'CCF_table'
    CCF_CNAME = Column(String(8), CheckConstraint('LENGTH("CCF_CNAME") <= 8'), primary_key=True, nullable=False)
    CCF_DESCR = Column(String(24), CheckConstraint('LENGTH("CCF_DESCR") <= 24'), nullable=False)
    CCF_DESCR2 = Column(String(64),
                        CheckConstraint('LENGTH("CCF_DESCR2") <= 64'))  # field will not be used by SCOS-2000
    CCF_CTYPE = Column(String(8), CheckConstraint('LENGTH("CCF_CTYPE") <= 8'))
    CCF_CRITICAL = Column(String(1), CheckConstraint('LENGTH("CCF_CRITICAL") <= 1'))
    CCF_PKTID = Column(String(8), CheckConstraint('LENGTH("CCF_PKTID") <= 8'), ForeignKey('TCP_table.TCP_ID'),
                       nullable=False)
    CCF_TYPE = Column(Integer, CheckConstraint("CCF_TYPE < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("CCF_TYPE") <= 3'))
    CCF_STYPE = Column(Integer, CheckConstraint("CCF_STYPE < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CCF_STYPE") <= 3'))
    CCF_APID = Column(Integer, CheckConstraint("CCF_APID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("CCF_APID") <= 5'))
    CCF_NPARS = Column(Integer, CheckConstraint("CCF_NPARS < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CCF_NPARS") <= 3'))  # field will not be used by SCOS-2000
    CCF_PLAN = Column(String(1), CheckConstraint('LENGTH("CCF_PLAN") <= 1'))
    CCF_EXEC = Column(String(1), CheckConstraint('LENGTH("CCF_EXEC") <= 1'))
    CCF_ILSCOPE = Column(String(1), CheckConstraint('LENGTH("CCF_ILSCOPE") <= 1'))
    CCF_ILSTAGE = Column(String(1), CheckConstraint('LENGTH("CCF_ILSTAGE") <= 1'))
    CCF_SUBSYS = Column(Integer, CheckConstraint("CCF_SUBSYS < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("CCF_SUBSYS") <= 3'))
    CCF_HIPRI = Column(String(1), CheckConstraint('LENGTH("CCF_HIPRI") <= 1'))
    CCF_MAPID = Column(Integer, CheckConstraint("CCF_MAPID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CCF_MAPID") <= 2'))
    CCF_DEFSET = Column(String(8), CheckConstraint('LENGTH("CCF_DEFSET") <= 8'), ForeignKey('PSV_table.PSV_PVSID'))
    CCF_RAPID = Column(Integer, CheckConstraint("CCF_RAPID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CCF_RAPID") <= 5'))
    CCF_ACK = Column(Integer, CheckConstraint("CCF_ACK < %d" % sys.maxsize), CheckConstraint('LENGTH("CCF_ACK") <= 2'))
    CCF_SUBSCHEDID = Column(Integer, CheckConstraint("CCF_SUBSCHEDID < %d" % sys.maxsize),
                            CheckConstraint('LENGTH("CCF_SUBSCHEDID") <= 5'))

    # PSM_rel= relationship("PSM", back_populates= 'CCF_rel')
    TCP_rel = relationship("TCP", back_populates='CCF_rel')
    CDF_rel = relationship("CDF", back_populates='CCF_rel', cascade="delete, all")
    CVP_rel = relationship("CVP", back_populates='CCF_rel', cascade="delete, all")
    # CSS_rel= relationship("CSS", back_populates= 'CCF_rel')
    PTV_rel = relationship("PTV", back_populates='CCF_rel', cascade="delete, all")
    PSV_rel = relationship("PSV", back_populates='CCF_rel')

    integer_maxlen = {
        'CCF_TYPE': 3,
        'CCF_STYPE': 3,
        'CCF_APID': 5,
        'CCF_NPARS': 3,
        'CCF_SUBSYS': 3,
        'CCF_MAPID': 2,
        'CCF_RAPID': 5,
        'CCF_ACK': 2,
        'CCF_SUBSCHEDID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CCF(
            CCF_CNAME=None,
            CCF_DESCR=None,
            CCF_DESCR2=None,
            CCF_CTYPE=None,
            CCF_CRITICAL=None,
            CCF_PKTID=None,
            CCF_TYPE=None,
            CCF_STYPE=None,
            CCF_APID=None,
            CCF_NPARS=None,
            CCF_PLAN=None,
            CCF_EXEC=None,
            CCF_ILSCOPE=None,
            CCF_ILSTAGE=None,
            CCF_SUBSYS=None,
            CCF_HIPRI=None,
            CCF_MAPID=None,
            CCF_DEFSET=None,
            CCF_RAPID=None,
            CCF_ACK=None,
            CCF_SUBSCHEDID=None
        )
        return object1


class CSF(Base):
    __tablename__ = 'CSF_table'
    CSF_NAME = Column(String(8), CheckConstraint('LENGTH("CSF_NAME") <= 8'), primary_key=True, nullable=False)
    CSF_DESC = Column(String(24), CheckConstraint('LENGTH("CSF_DESC") <= 24'))
    CSF_DESC2 = Column(String(64), CheckConstraint('LENGTH("CSF_DESC2") <= 64'))  # field will not be used by SCOS-2000
    CSF_IFTT = Column(String(1), CheckConstraint('LENGTH("CSF_IFTT") <= 1'))
    CSF_NFPARS = Column(Integer, CheckConstraint("CSF_NFPARS < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("CSF_NFPARS") <= 3'))
    CSF_ELEMS = Column(Integer, CheckConstraint("CSF_ELEMS < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CSF_ELEMS") <= 5'))  # field will not be used by SCOS-2000
    CSF_CRITICAL = Column(String(1), CheckConstraint('LENGTH("CSF_CRITICAL") <= 1'))
    CSF_PLAN = Column(String(1), CheckConstraint('LENGTH("CSF_PLAN") <= 1'))
    CSF_EXEC = Column(String(1), CheckConstraint('LENGTH("CSF_EXEC") <= 1'))
    CSF_SUBSYS = Column(Integer, CheckConstraint("CSF_SUBSYS < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("CSF_SUBSYS") <= 3'))
    CSF_GENTIME = Column(String(17),
                         CheckConstraint('LENGTH("CSF_GENTIME") <= 17'))  # field will not be used by SCOS-2000
    CSF_DOCNAME = Column(String(32),
                         CheckConstraint('LENGTH("CSF_DOCNAME") <= 32'))  # field will not be used by SCOS-2000
    CSF_ISSUE = Column(String(10), CheckConstraint('LENGTH("CSF_ISSUE") <= 10'))  # field will not be used by SCOS-2000
    CSF_DATE = Column(String(17), CheckConstraint('LENGTH("CSF_DATE") <= 17'))  # field will not be used by SCOS-2000
    CSF_DEFSET = Column(String(8), CheckConstraint('LENGTH("CSF_DEFSET") <= 8'), ForeignKey('PSV_table.PSV_PVSID'))
    CSF_SUBSCHEDID = Column(Integer, CheckConstraint("CSF_SUBSCHEDID < %d" % sys.maxsize),
                            CheckConstraint('LENGTH("CSF_SUBSCHEDID") <= 5'))

    # PSM_rel= relationship("PSM", back_populates= 'CSF_rel')
    CSP_rel = relationship("CSP", back_populates="CSF_rel", cascade="delete, all")
    PSV_rel = relationship("PSV", back_populates="CSF_rel")
    CSS_rel = relationship("CSS", back_populates="CSF_rel", cascade="delete, all")

    integer_maxlen = {
        'CSF_NFPARS': 3,
        'CSF_ELEMS': 5,
        'CSF_SUBSYS': 3,
        'CSF_SUBSCHEDID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CSF(
            CSF_NAME=None,
            CSF_DESC=None,
            CSF_DESC2=None,
            CSF_IFTT=None,
            CSF_NFPARS=None,
            CSF_ELEMS=None,
            CSF_CRITICAL=None,
            CSF_PLAN=None,
            CSF_EXEC=None,
            CSF_SUBSYS=None,
            CSF_GENTIME=None,
            CSF_DOCNAME=None,
            CSF_ISSUE=None,
            CSF_DATE=None,
            CSF_DEFSET=None,
            CSF_SUBSCHEDID=None
        )
        return object1


class CDF(Base):
    __tablename__ = 'CDF_table'
    CDF_CNAME = Column(String(8), CheckConstraint('LENGTH("CDF_CNAME") <= 8'), ForeignKey('CCF_table.CCF_CNAME'),
                       primary_key=True, nullable=False)
    CDF_ELTYPE = Column(String(1), CheckConstraint('LENGTH("CDF_ELTYPE") <= 1'), nullable=False)
    CDF_DESCR = Column(String(24), CheckConstraint('LENGTH("CDF_DESCR") <= 24'))
    CDF_ELLEN = Column(Integer, CheckConstraint("CDF_ELLEN < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CDF_ELLEN") <= 4'), nullable=False)
    CDF_BIT = Column(Integer, CheckConstraint("CDF_BIT < %d" % sys.maxsize), CheckConstraint('LENGTH("CDF_BIT") <= 4'),
                     primary_key=True, nullable=False)
    CDF_GRPSIZE = Column(Integer, CheckConstraint("CDF_GRPSIZE < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("CDF_GRPSIZE") <= 2'))
    CDF_PNAME = Column(String(8), CheckConstraint('LENGTH("CDF_PNAME") <= 8'),
                       ForeignKey('CPC_table.CPC_PNAME'))  # any other foreign key?
    CDF_INTER = Column(String(1), CheckConstraint('LENGTH("CDF_INTER") <= 1'))
    CDF_VALUE = Column(String)
    CDF_TMID = Column(String(8), CheckConstraint('LENGTH("CDF_TMID") <= 8'))

    # PVS_rel= relationship("PVS", back_populates= 'CDF_rel')
    CPC_rel = relationship("CPC", back_populates='CDF_rel')
    # SDF_rel= relationship("SDF", back_populates= 'CDF_rel')
    CCF_rel = relationship("CCF", back_populates='CDF_rel')

    integer_maxlen = {
        'CDF_ELLEN': 4,
        'CDF_BIT': 4,
        'CDF_GRPSIZE': 2
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CDF(
            CDF_CNAME=None,
            CDF_ELTYPE=None,
            CDF_DESCR=None,
            CDF_ELLEN=None,
            CDF_BIT=None,
            CDF_GRPSIZE=None,
            CDF_PNAME=None,
            CDF_INTER=None,
            CDF_VALUE=None,
            CDF_TMID=None
        )
        return object1


class PST(Base):
    __tablename__ = 'PST_table'
    PST_NAME = Column(String(8), CheckConstraint('LENGTH("PST_NAME") <= 8'), primary_key=True, nullable=False)
    PST_DESCR = Column(String(24), CheckConstraint('LENGTH("PST_DESCR") <= 24'))

    PSM_rel = relationship("PSM", uselist=False, back_populates="PST_rel")
    PSV_rel = relationship("PSV", uselist=False, back_populates="PST_rel", cascade="delete, all")

    @classmethod
    def createEmptyObject(self):
        object1 = PST(
            PST_NAME=None,
            PST_DESCR=None
        )
        return object1


class PSV(Base):
    __tablename__ = 'PSV_table'
    PSV_NAME = Column(String(8), CheckConstraint('LENGTH("PSV_NAME") <= 8'), ForeignKey('PST_table.PST_NAME'),
                      nullable=False)
    PSV_PVSID = Column(String(8), CheckConstraint('LENGTH("PSV_PVSID") <= 8'), nullable=False, primary_key=True)
    PSV_DESCR = Column(String(24), CheckConstraint('LENGTH("PSV_DESCR") <= 24'))

    CCF_rel = relationship("CCF", back_populates='PSV_rel')
    CSF_rel = relationship("CSF", back_populates='PSV_rel')
    PST_rel = relationship("PST", back_populates='PSV_rel')
    PVS_rel = relationship("PVS", uselist=False, back_populates="PSV_rel", cascade="delete, all")
    SDF_rel = relationship("SDF", uselist=False, back_populates="PSV_rel", cascade="delete, all")

    @classmethod
    def createEmptyObject(self):
        object1 = PSV(
            PSV_NAME=None,
            PSV_PVSID=None,
            PSV_DESCR=None
        )
        return object1


class PVS(Base):
    __tablename__ = 'PVS_table'
    PVS_ID = Column(String(8), CheckConstraint('LENGTH("PVS_ID") <= 8'),
                    ForeignKey('PSV_table.PSV_PVSID'),
                    primary_key=True, nullable=False)
    PVS_PSID = Column(String(8), CheckConstraint('LENGTH("PVS_PSID") <= 8'), nullable=False)
    PVS_PNAME = Column(String(8), CheckConstraint('LENGTH("PVS_PNAME") <= 8'),
                       nullable=False)  # ForeignKey('CDF_table.CDF_PNAME'),  ForeignKey('CSP_table.CSP_FPNAME')
    PVS_INTER = Column(String(1), CheckConstraint('LENGTH("PVS_INTER") <= 1'))
    PVS_VALS = Column(String)
    PVS_BIT = Column(Integer, CheckConstraint("PVS_BIT < %d" % sys.maxsize),
                     CheckConstraint('LENGTH("PVS_BIT") <= 4'),
                     primary_key=True, nullable=False)

    PSV_rel = relationship("PSV", back_populates="PVS_rel")
    # CDF_rel= relationship("CDF", back_populates= "PVS_rel")
    # CSP_rel= relationship("CSP", back_populates= "PVS_rel")

    integer_maxlen = {
        'PVS_BIT': 4
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PVS(
            PVS_ID=None,
            PVS_PSID=None,
            PVS_PNAME=None,
            PVS_INTER=None,
            PVS_VALS=None,
            PVS_BIT=None
        )
        return object1


class PSM(Base):
    __tablename__ = 'PSM_table'
    PSM_NAME = Column(String(8), CheckConstraint('LENGTH("PSM_NAME") <= 8'), primary_key=True,
                      nullable=False)  # ForeignKey('CSF_table.CSF_NAME'), ForeignKey('CCF_table.CCF_CNAME')
    PSM_TYPE = Column(String(1), CheckConstraint('LENGTH("PSM_TYPE") <= 1'), primary_key=True, nullable=False)
    PSM_PARSET = Column(String(8), CheckConstraint('LENGTH("PSM_PARSET") <= 8'), ForeignKey('PST_table.PST_NAME'),
                        primary_key=True, nullable=False)

    PST_rel = relationship("PST", back_populates="PSM_rel")

    # CSF_rel= relationship("CSF", back_populates= 'PSM_rel')
    # CCF_rel= relationship("CCF", back_populates= "PSM_rel")

    @classmethod
    def createEmptyObject(self):
        object1 = PSM(
            PSM_NAME=None,
            PSM_TYPE=None,
            PSM_PARSET=None
        )
        return object1


class SDF(Base):
    __tablename__ = 'SDF_table'
    SDF_SQNAME = Column(String(8), CheckConstraint('LENGTH("SDF_SQNAME") <= 8'), primary_key=True, nullable=False)
    SDF_ENTRY = Column(Integer, CheckConstraint("SDF_ENTRY < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("SDF_ENTRY") <= 5'), primary_key=True, nullable=False)
    SDF_ELEMID = Column(String(8), CheckConstraint('LENGTH("SDF_ELEMID") <= 8'), nullable=False)
    SDF_POS = Column(Integer, CheckConstraint("SDF_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("SDF_POS") <= 4'),
                     primary_key=True, nullable=False)
    SDF_PNAME = Column(String(8), CheckConstraint('LENGTH("SDF_PNAME") <= 8'), primary_key=True,
                       nullable=False)  # ForeignKey('CSP_table.CSP_FPNAME'), ForeignKey('CDF_table.CDF_PNAME')
    SDF_FTYPE = Column(String(1), CheckConstraint('LENGTH("SDF_FTYPE") <= 1'))
    SDF_VTYPE = Column(String(1), CheckConstraint('LENGTH("SDF_VTYPE") <= 1'), nullable=False)
    SDF_VALUE = Column(String, ForeignKey('CSP_table.CSP_FPNAME'))
    SDF_VALSET = Column(String(8), CheckConstraint('LENGTH("SDF_VALSET") <= 8'), ForeignKey('PSV_table.PSV_PVSID'))
    SDF_REPPOS = Column(Integer, CheckConstraint("SDF_REPPOS < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("SDF_REPPOS") <= 4'))

    PSV_rel = relationship("PSV", back_populates="SDF_rel")
    # CDF_rel= relationship("CDF", back_populates= "SDF_rel")
    CSP_rel = relationship("CSP", back_populates="SDF_rel")

    integer_maxlen = {
        'SDF_ENTRY': 5,
        'SDF_POS': 4,
        'SDF_REPPOS': 4
    }

    @classmethod
    def createEmptyObject(self):
        object1 = SDF(
            SDF_SQNAME=None,
            SDF_ENTRY=None,
            SDF_ELEMID=None,
            SDF_POS=None,
            SDF_PNAME=None,
            SDF_FTYPE=None,
            SDF_VTYPE=None,
            SDF_VALUE=None,
            SDF_VALSET=None,
            SDF_REPPOS=None,
        )
        return object1


class CSP(Base):
    __tablename__ = 'CSP_table'
    CSP_SQNAME = Column(String(8), CheckConstraint('LENGTH("CSP_SQNAME") <= 8'), ForeignKey("CSF_table.CSF_NAME"),
                        primary_key=True, nullable=False)
    CSP_FPNAME = Column(String(8), CheckConstraint('LENGTH("CSP_FPNAME") <= 8'), primary_key=True, nullable=False)
    CSP_FPNUM = Column(Integer, CheckConstraint("CSP_FPNUM < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CSP_FPNUM") <= 5'), nullable=False)
    CSP_DESCR = Column(String(24), CheckConstraint('LENGTH("CSP_DESCR") <= 24'))
    CSP_PTC = Column(Integer, CheckConstraint("CSP_PTC < %d" % sys.maxsize), CheckConstraint('LENGTH("CSP_PTC") <= 2'),
                     nullable=False)
    CSP_PFC = Column(Integer, CheckConstraint("CSP_PFC < %d" % sys.maxsize), CheckConstraint('LENGTH("CSP_PFC") <= 5'),
                     nullable=False)
    CSP_DISPFMT = Column(String(1), CheckConstraint('LENGTH("CSP_DISPFMT") <= 1'))
    CSP_RADIX = Column(String(1), CheckConstraint('LENGTH("CSP_RADIX") <= 1'))
    CSP_TYPE = Column(String(1), CheckConstraint('LENGTH("CSP_TYPE") <= 1'), nullable=False)
    CSP_VTYPE = Column(String(1), CheckConstraint('LENGTH("CSP_VTYPE") <= 1'))
    CSP_DEFVAL = Column(String)
    CSP_CATEG = Column(String(1), CheckConstraint('LENGTH("CSP_CATEG") <= 1'))
    CSP_PRFREF = Column(String(10), CheckConstraint('LENGTH("CSP_PRFREF") <= 10'), ForeignKey('PRF_table.PRF_NUMBR'))
    CSP_CCAREF = Column(String(10), CheckConstraint('LENGTH("CSP_CCAREF") <= 10'), ForeignKey('CCA_table.CCA_NUMBR'))
    CSP_PAFREF = Column(String(10), CheckConstraint('LENGTH("CSP_PAFREF") <= 10'), ForeignKey('PAF_table.PAF_NUMBR'))
    CSP_UNIT = Column(String(4), CheckConstraint('LENGTH("CSP_UNIT") <= 4'))

    CCA_rel = relationship("CCA", back_populates='CSP_rel')
    PRF_rel = relationship("PRF", back_populates='CSP_rel')
    PAF_rel = relationship("PAF", back_populates='CSP_rel')
    CSF_rel = relationship("CSF", back_populates='CSP_rel')
    SDF_rel = relationship("SDF", back_populates='CSP_rel', cascade="delete, all")
    # PVS_rel= relationship("PVS", back_populates= 'CSP_rel')

    integer_maxlen = {
        'CSP_FPNUM': 5,
        'CSP_PTC': 2,
        'CSP_PFC': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CSP(
            CSP_SQNAME=None,
            CSP_FPNAME=None,
            CSP_FPNUM=None,
            CSP_DESCR=None,
            CSP_PTC=None,
            CSP_PFC=None,
            CSP_DISPFMT=None,
            CSP_RADIX=None,
            CSP_TYPE=None,
            CSP_VTYPE=None,
            CSP_DEFVAL=None,
            CSP_CATEG=None,
            CSP_PRFREF=None,
            CSP_CCAREF=None,
            CSP_PAFREF=None,
            CSP_UNIT=None
        )
        return object1


"""Command and Sequence Parameter tables (Figure 6)"""


# PVS
# SDF
# CDF

class CPC(Base):
    __tablename__ = 'CPC_table'
    CPC_PNAME = Column(String(8), CheckConstraint('LENGTH("CPC_PNAME") <= 8'), primary_key=True, nullable=False)
    CPC_DESCR = Column(String(24), CheckConstraint('LENGTH("CPC_DESCR") <= 24'))
    CPC_PTC = Column(Integer, CheckConstraint("CPC_PTC < %d" % sys.maxsize), CheckConstraint('LENGTH("CPC_PTC") <= 2'),
                     primary_key=True, nullable=False)
    CPC_PFC = Column(Integer, CheckConstraint("CPC_PFC < %d" % sys.maxsize), CheckConstraint('LENGTH("CPC_PFC") <= 5'),
                     primary_key=True, nullable=False)
    CPC_DISPFMT = Column(String(1), CheckConstraint('LENGTH("CPC_DISPFMT") <= 1'))
    CPC_RADIX = Column(String(1), CheckConstraint('LENGTH("CPC_RADIX") <= 1'))
    CPC_UNIT = Column(String(4), CheckConstraint('LENGTH("CPC_UNIT") <= 4'))
    CPC_CATEG = Column(String(1), CheckConstraint('LENGTH("CPC_CATEG") <= 1'))
    CPC_PRFREF = Column(String(10), CheckConstraint('LENGTH("CPC_PRFREF") <= 10'), ForeignKey('PRF_table.PRF_NUMBR'))
    CPC_CCAREF = Column(String(10), CheckConstraint('LENGTH("CPC_CCAREF") <= 10'), ForeignKey('CCA_table.CCA_NUMBR'))
    CPC_PAFREF = Column(String(10), CheckConstraint('LENGTH("CPC_PAFREF") <= 10'), ForeignKey('PAF_table.PAF_NUMBR'))
    CPC_INTER = Column(String(1), CheckConstraint('LENGTH("CPC_INTER") <= 1'))
    CPC_DEFVAL = Column(String)
    CPC_CORR = Column(String(1), CheckConstraint('LENGTH("CPC_CORR") <= 1'))
    CPC_OBTID = Column(Integer, CheckConstraint("CPC_OBTID < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("CPC_OBTID") <= 5'))
    CPC_ENDIAN = Column(String(1), CheckConstraint('LENGTH("CPC_ENDIAN") <= 1'))  # field will not be used by SCOS-2000

    CCA_rel = relationship("CCA", back_populates='CPC_rel')
    PRF_rel = relationship("PRF", back_populates='CPC_rel')
    PAF_rel = relationship("PAF", back_populates='CPC_rel')
    CDF_rel = relationship("CDF", back_populates='CPC_rel')

    integer_maxlen = {
        'CPC_PTC': 2,
        'CPC_PFC': 5,
        'CPC_OBTID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CPC(
            CPC_PNAME=None,
            CPC_DESCR=None,
            CPC_PTC=None,
            CPC_PFC=None,
            CPC_DISPFMT=None,
            CPC_RADIX=None,
            CPC_UNIT=None,
            CPC_CATEG=None,
            CPC_PRFREF=None,
            CPC_CCAREF=None,
            CPC_PAFREF=None,
            CPC_INTER=None,
            CPC_DEFVAL=None,
            CPC_CORR=None,
            CPC_OBTID=None,
            CPC_ENDIAN=None
        )
        return object1


# CSP
# CSF

class CCA(Base):
    __tablename__ = 'CCA_table'
    CCA_NUMBR = Column(String(10), CheckConstraint('LENGTH("CCA_NUMBR") <= 10'), primary_key=True, nullable=False)
    CCA_DESCR = Column(String(24), CheckConstraint('LENGTH("CCA_DESCR") <= 24'))
    CCA_ENGFMT = Column(String(1), CheckConstraint('LENGTH("CCA_ENGFMT") <= 1'))
    CCA_RAWFMT = Column(String(1), CheckConstraint('LENGTH("CCA_RAWFMT") <= 1'))
    CCA_RADIX = Column(String(1), CheckConstraint('LENGTH("CCA_RADIX") <= 1'))
    CCA_UNIT = Column(String(4), CheckConstraint('LENGTH("CCA_UNIT") <= 4'))  # field will not be used by SCOS-2000
    CCA_NCURVE = Column(Integer, CheckConstraint("CCA_NCURVE < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("CCA_NCURVE") <= 3'))  # field will not be used by SCOS-2000

    CCS_rel = relationship("CCS", back_populates='CCA_rel', cascade="delete, all")
    CPC_rel = relationship("CPC", back_populates='CCA_rel')
    CSP_rel = relationship("CSP", back_populates='CCA_rel', cascade="delete, all")

    integer_maxlen = {
        'CCA_NCURVE': 3
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CCA(
            CCA_NUMBR=None,
            CCA_DESCR=None,
            CCA_ENGFMT=None,
            CCA_RAWFMT=None,
            CCA_RADIX=None,
            CCA_UNIT=None,
            CCA_NCURVE=None
        )
        return object1


class PAF(Base):
    __tablename__ = 'PAF_table'
    PAF_NUMBR = Column(String(10), CheckConstraint('LENGTH("PAF_NUMBR") <= 10'), primary_key=True, nullable=False)
    PAF_DESCR = Column(String(24), CheckConstraint('LENGTH("PAF_DESCR") <= 24'))
    PAF_RAWFMT = Column(String(1), CheckConstraint('LENGTH("PAF_RAWFMT") <= 1'))
    PAF_NALIAS = Column(Integer, CheckConstraint("PAF_NALIAS < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("PAF_NALIAS") <= 3'))  # field will not be used by SCOS-2000

    PAS_rel = relationship("PAS", back_populates="PAF_rel", cascade="delete, all")
    CPC_rel = relationship("CPC", back_populates="PAF_rel")
    CSP_rel = relationship("CSP", back_populates="PAF_rel", cascade="delete, all")

    integer_maxlen = {
        'PAF_NALIAS': 3
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PAF(
            PAF_NUMBR=None,
            PAF_DESCR=None,
            PAF_RAWFMT=None,
            PAF_NALIAS=None
        )
        return object1


class PRF(Base):
    __tablename__ = 'PRF_table'
    PRF_NUMBR = Column(String(10), CheckConstraint('LENGTH("PRF_NUMBR") <= 10'), primary_key=True, nullable=False)
    PRF_DESCR = Column(String(24), CheckConstraint('LENGTH("PRF_DESCR") <= 24'))
    PRF_INTER = Column(String(1), CheckConstraint('LENGTH("PRF_INTER") <= 1'))
    PRF_DSPFMT = Column(String(1), CheckConstraint('LENGTH("PRF_DSPFMT") <= 1'))
    PRF_RADIX = Column(String(1), CheckConstraint('LENGTH("PRF_RADIX") <= 1'))
    PRF_NRANGE = Column(Integer, CheckConstraint("PRF_NRANGE < %d" % sys.maxsize),
                        CheckConstraint('LENGTH("PRF_NRANGE") <= 3'))  # field will not be used by SCOS-2000
    PRF_UNIT = Column(String(4), CheckConstraint('LENGTH("PRF_UNIT") <= 4'))  # field will not be used by SCOS-2000

    PRV_rel = relationship('PRV', back_populates='PRF_rel', cascade="delete, all")
    CPC_rel = relationship('CPC', back_populates='PRF_rel')
    CSP_rel = relationship('CSP', back_populates='PRF_rel', cascade="delete, all")

    integer_maxlen = {
        'PRF_NRANGE': 3
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PRF(
            PRF_NUMBR=None,
            PRF_DESCR=None,
            PRF_INTER=None,
            PRF_DSPFMT=None,
            PRF_RADIX=None,
            PRF_NRANGE=None,
            PRF_UNIT=None,
        )
        return object1


class CCS(Base):
    __tablename__ = 'CCS_table'
    CCS_NUMBR = Column(String(10), CheckConstraint('LENGTH("CCS_NUMBR") <= 10'), ForeignKey('CCA_table.CCA_NUMBR'),
                       primary_key=True, nullable=False)
    CCS_XVALS = Column(String)
    CCS_YVALS = Column(String, primary_key=True, nullable=False)

    CCA_rel = relationship("CCA", back_populates="CCS_rel")

    @classmethod
    def createEmptyObject(self):
        object1 = CCS(
            CCS_NUMBR=None,
            CCS_XVALS=None,
            CCS_YVALS=None
        )
        return object1


class PAS(Base):
    __tablename__ = 'PAS_table'
    PAS_NUMBR = Column(String(10), CheckConstraint('LENGTH("PAS_NUMBR") <= 10'), ForeignKey("PAF_table.PAF_NUMBR"),
                       primary_key=True, nullable=False)
    PAS_ALTXT = Column(String, nullable=False)
    PAS_ALVAL = Column(String, primary_key=True, nullable=False)

    PAF_rel = relationship("PAF", back_populates="PAS_rel")

    @classmethod
    def createEmptyObject(self):
        object1 = PAS(
            PAS_NUMBR=None,
            PAS_ALTXT=None,
            PAS_ALVAL=None
        )
        return object1


class PRV(Base):
    __tablename__ = 'PRV_table'
    PRV_NUMBR = Column(String(10), CheckConstraint('LENGTH("PRV_NUMBR") <= 10'), ForeignKey('PRF_table.PRF_NUMBR'),
                       primary_key=True, nullable=False)
    PRV_MINVAL = Column(String, primary_key=True, nullable=False)
    PRV_MAXVAL = Column(String)

    PRF_rel = relationship('PRF', back_populates='PRV_rel')

    @classmethod
    def createEmptyObject(self):
        object1 = PRV(
            PRV_NUMBR=None,
            PRV_MAXVAL=None,
            PRV_MINVAL=None
        )
        self.PRV_NUMBR = None
        self.PRV_MINVAL = None
        self.PRV_MAXVAL = None
        return object1  # <class '__main__.PRV'>
    # return self # <class 'sqlalchemy.ext.declarative.api.DeclarativeMeta'>


"""Tables with no relation to other tables"""


class CPS(Base):  # table not required for the processing within SCOS-2000
    __tablename__ = 'CPS_table'
    CPS_NAME = Column(String(8), CheckConstraint('LENGTH("CPS_NAME") <= 8'), primary_key=True, nullable=False)
    CPS_PAR = Column(String(8), CheckConstraint('LENGTH("CPS_PARS") <= 8'), nullable=False)
    CPS_BIT = Column(Integer, CheckConstraint("CPS_BIT < %d" % sys.maxsize), CheckConstraint('LENGTH("CPS_BIT") <= 4'),
                     primary_key=True, nullable=False)

    integer_maxlen = {
        'CPS_BIT': 4
    }

    @classmethod
    def createEmptyObject(self):
        object1 = CPS(
            CPS_NAME=None,
            CPS_PAR=None,
            CPS_BIT=None
        )
        return object1


class DST(Base):  # optional table
    __tablename__ = 'DST_table'
    DST_APID = Column(Integer, CheckConstraint("DST_APID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("DST_APID") <= 5'), primary_key=True, nullable=False)
    DST_ROUTE = Column(String(30), CheckConstraint('LENGTH("DST_ROUTE") <= 30'), nullable=False)

    integer_maxlen = {
        'DST_APID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = DST(
            DST_APID=None,
            DST_ROUTE=None
        )
        return object1


class PIC(Base):
    __tablename__ = 'PIC_table'
    PIC_TYPE = Column(Integer, CheckConstraint("PIC_TYPE < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PIC_TYPE") <= 3'), primary_key=True, nullable=False)
    PIC_STYPE = Column(Integer, CheckConstraint("PIC_STYPE < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("PIC_STYPE") <= 3'), primary_key=True, nullable=False)
    PIC_PI1_OFF = Column(Integer, CheckConstraint("PIC_PI1_OFF < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PIC_PI1_OFF") <= 5'), nullable=False)
    PIC_PI1_WID = Column(Integer, CheckConstraint("PIC_PI1_WID < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PIC_PI1_WID") <= 3'), nullable=False)
    PIC_PI2_OFF = Column(Integer, CheckConstraint("PIC_PI2_OFF < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PIC_PI2_OFF") <= 5'), nullable=False)
    PIC_PI2_WID = Column(Integer, CheckConstraint("PIC_PI2_WID < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("PIC_PI2_WID") <= 3'), nullable=False)
    PIC_APID = Column(Integer, CheckConstraint("PIC_APID < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PIC_APID") <= 5'))  # primary_key ??

    integer_maxlen = {
        'PIC_TYPE': 3,
        'PIC_STYPE': 3,
        'PIC_PI1_OFF': 5,
        'PIC_PI1_WID': 3,
        'PIC_PI2_OFF': 5,
        'PIC_PI2_WID': 3,
        'PIC_APID': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PIC(
            PIC_TYPE=None,
            PIC_STYPE=None,
            PIC_PI1_OFF=None,
            PIC_PI1_WID=None,
            PIC_PI2_OFF=None,
            PIC_PI2_WID=None,
            PIC_APID=None
        )
        return object1


class VDF(Base):
    __tablename__ = 'VDF_table'
    """Apparently, there is no primary key, so VDF_NAME and VDF_COMMENT have been chosen"""
    VDF_NAME = Column(String(8), CheckConstraint('LENGTH("VDF_NAME") <= 8'), nullable=False, primary_key=True)
    VDF_COMMENT = Column(String(32), CheckConstraint('LENGTH("VDF_COMMENT") <= 32'), nullable=False, primary_key=True)
    VDF_DOMAINID = Column(Integer, CheckConstraint("VDF_DOMAINID < %d" % sys.maxsize),
                          CheckConstraint('LENGTH("VDF_DOMAINID") <= 5'))
    VDF_RELEASE = Column(Integer, CheckConstraint("VDF_RELEASE < %d" % sys.maxsize),
                         CheckConstraint('LENGTH("VDF_RELEASE") <= 5'))
    VDF_ISSUE = Column(Integer, CheckConstraint("VDF_ISSUE < %d" % sys.maxsize),
                       CheckConstraint('LENGTH("VDF_ISSUE") <= 5'))

    integer_maxlen = {
        'VDF_DOMAINID': 5,
        'VDF_RELEASE': 5,
        'VDF_ISSUE': 5
    }

    @classmethod
    def createEmptyObject(self):
        object1 = VDF(
            VDF_NAME=None,
            VDF_COMMENT=None,
            VDF_DOMAINID=None,
            VDF_RELEASE=None,
            VDF_ISSUE=None
        )
        return object1


class PPF(Base):  # table not required for the processing within SCOS-2000
    __tablename__ = 'PPF_table'
    PPF_NUMBE = Column(String(4), CheckConstraint('LENGTH("PPF_NUMBE") <= 4'), nullable=False, primary_key=True)
    PPF_HEAD = Column(String(32), CheckConstraint('LENGTH("PPF_HEAD") <= 32'))
    PPF_NBPR = Column(Integer, CheckConstraint("PPF_NBPR < %d" % sys.maxsize),
                      CheckConstraint('LENGTH("PPF_NBPR") <= 2'))

    integer_maxlen = {
        'PPF_NBPR': 2,
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PPF(
            PPF_NUMBE=None,
            PPF_HEAD=None,
            PPF_NBPR=None
        )
        return object1


class PPC(Base):  # table not required for the processing within SCOS-2000
    __tablename__ = 'PPC_table'
    PPC_NUMBE = Column(String(4), CheckConstraint('LENGTH("PPC_NUMBE") <= 4'), nullable=False, primary_key=True)
    PPC_POS = Column(Integer, CheckConstraint("PPC_POS < %d" % sys.maxsize), CheckConstraint('LENGTH("PPC_POS") <= 32'),
                     nullable=False, primary_key=True)
    PPC_NAME = Column(String(8), CheckConstraint('LENGTH("PPC_NAME") <= 8'), nullable=False)
    PPC_FORM = Column(String(1), CheckConstraint('LENGTH("PPC_FORM") <= 1'))

    integer_maxlen = {
        'PPC_POS': 2,
    }

    @classmethod
    def createEmptyObject(self):
        object1 = PPC(
            PPC_NUMBE=None,
            PPC_POS=None,
            PPC_NAME=None,
            PPC_FORM=None
        )
        return object1


# SCO: not listed in the document
# TCD: not listed in the document
# TMD: not listed in the document

class SCO:
    __tablename__ = 'SCO_table'


class TCD:
    __tablename__ = 'TCD_table'


class TMD:
    __tablename__ = 'TMD_table'


tablename_list = ['CSS', 'CCF', 'CSF', 'PSM', 'PSV', 'SDF', 'CDF', 'CSP', 'CPS', 'DST',  # list with all the table names
                  'PIC', 'SCO', 'TCD', 'TMD', 'VDF', 'CAF', 'CAP', 'CCA', 'CCS', 'CUR', 'CVE', 'CVP',
                  'CVS', 'DPC', 'DPF', 'GPC', 'GPF', 'GRP', 'GRPA', 'GRPK', 'LGF', 'MCF', 'OCF',
                  'OCP', 'PAF', 'PAS', 'PCDF', 'PCPC', 'PID', 'PLF', 'PRF', 'PRV', 'PST', 'PTV', 'SPC',
                  'SPF', 'TCP', 'TPCF', 'TXF', 'TXP', 'VPD', 'CPC', 'PCF', 'PVS', "PPF", "PPC"]

tablename_dict = {'CSS': CSS, 'CCF': CCF, 'CSF': CSF, 'PSM': PSM, 'PSV': PSV, 'SDF': SDF,
                  # dictionary associating table names with classes
                  'CDF': CDF, 'CSP': CSP, 'CPS': CPS, 'DST': DST, 'PIC': PIC, 'SCO': SCO, 'TCD': TCD,
                  'TMD': TMD, 'VDF': VDF, 'CAF': CAF, 'CAP': CAP, 'CCA': CCA, 'CCS': CCS, 'CUR': CUR,
                  'CVE': CVE, 'CVP': CVP, 'CVS': CVS, 'DPC': DPC, 'DPF': DPF, 'GPC': GPC, 'GPF': GPF,
                  'GRP': GRP, 'GRPA': GRPA, 'GRPK': GRPK, 'LGF': LGF, 'MCF': MCF, 'OCF': OCF, 'OCP': OCP,
                  'PAF': PAF, 'PAS': PAS, 'PCDF': PCDF, 'PCPC': PCPC, 'PID': PID, 'PLF': PLF, 'PRF': PRF,
                  'PRV': PRV, 'PST': PST, 'PTV': PTV, 'SPC': SPC, 'SPF': SPF, 'TCP': TCP, 'TPCF': TPCF,
                  'TXF': TXF, 'TXP': TXP, 'VPD': VPD, 'CPC': CPC, 'PCF': PCF, 'PVS': PVS, "PPF": PPF, "PPC": PPC}

suggested_input_order = [  # order in which tables should be input
    "SCO", "TCD", "TMD", "CPS", "VDF", "PIC", "DPF", "GPF", "LGF", "MCF", "TCP", "TXF",
    "CAF", "CAP", "PST", "PSV", "TXP", "CCF", "CSF", "CSS", "PAS", "PAF", "DST", "PID",
    "CVS", "PCF", "VPD", "OCF", "OCP", "GRP", "GRPA", "GRPK", "PLF", "TPCF", "SPF", "SPC",
    "PCPC", "PCDF", "PSM", "PTV", "GPC", "CUR", "CVP", "DPC", "CCA", "CCS", "CPC", "CDF",
    "CVE", "PRF", "PRV", "CSP", "SDF", "PVS", "PPF", "PPC"]

# tables which are not supported by the application
not_supported_tables = ['SCO', 'TCD', 'TMD']

# dictionary associating each table with the order in which it should be added to the database
suggested_input_order_dict = {}
i = 0
for table in suggested_input_order:
    suggested_input_order_dict.update({table: i})
    i += 1


def attributeSetter(certain_object, field, value):
    """setter method that will be monkey patched"""
    certain_object.__dict__[field] = value


# print("__setattr__ entered")

def objectComparator(object1, object2):
    """eq method that will be monkey patched"""
    if type(object1) != type(object2):
        return False
    else:
        class1_type_str = object1.__tablename__.split('_')[0]
        class2_type_str = object2.__tablename__.split('_')[0]

        object1_dict = object1.__dict__
        object2_dict = object2.__dict__
        for key in object1_dict.keys():
            if key.split('_')[0] == class1_type_str:  # only compare attributtes that can be set by the user
                if str(object1_dict[key]) != str(object2_dict[key]):  # cast them in order to compare integers
                    return False

        return True


def objectPrinter(object1):
    """Prints an object"""
    class1_type_str = object1.__tablename__.split('_')[0]

    print_string = ''
    for key, value in object1.__dict__.items():
        if key.split('_')[0] == class1_type_str:
            print_string += "%s: \t%s\n" % (key, value)

    return print_string


for class_type in tablename_dict.values():  # Monkey patching
    class_type.__setattr__ = attributeSetter
    class_type.__eq__ = objectComparator
    class_type.__str__ = objectPrinter

if __name__ == '__main__':
    pass
