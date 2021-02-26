# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\Haydn\\PycharmProjects\\dimensionality-reduction-ui'],
             binaries=[],
             datas=[],
             hiddenimports=['menu', 'classification', 'reduction', 'data', 'fileObject', 'sklearn', 'sklearn.neighbors._typedefs', 'sklearn.utils._weight_vector', 'sklearn.utils', 'sklearn.neighbors._quad_tree'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [('v', None, 'OPTION')],
          name='main',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
