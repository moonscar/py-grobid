from distutils.core import setup

setup(
        name='grobid',     # 包名字
        version='0.1',   # 包版本
        description='GROBID is a machine learning library for extracting, parsing and re-structuring raw documents such as PDF into structured XML/TEI encoded documents with a particular focus on technical and scientific publications.',   # 简单描述
        author='moonscar',  # 作者
        install_requires=[
                "bs4",
                "english-words==1.1.0"]
        packages=["grobid"],
)