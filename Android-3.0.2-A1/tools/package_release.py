"""Package a verified Android release; never include private signing material."""
from pathlib import Path
import hashlib, json, shutil, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = Path.home() / 'Downloads/AutoTimelineSync-ANDROID-3.0.1'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def package():
    reports = {}
    for name in ('API30', 'API35'):
        data = json.loads((ROOT / 'Verification' / name / 'results.json').read_text())
        if data['failures'] or data['count'] < 35:
            raise RuntimeError(f'{name}: final verification did not pass')
        reports[name] = data
    DELIVERY.mkdir(parents=True, exist_ok=True)
    apk = ROOT / 'AutoTimelineSync-3.0.1-ANDROID.apk'
    shutil.copy2(apk, DELIVERY / apk.name)
    for name in ('README.md', 'DECISIONS.md', 'VERIFICATION_REPORT.md'):
        shutil.copy2(ROOT / name, DELIVERY / name)
    source = DELIVERY / 'AutoTimelineSync-3.0.1-ANDROID-SOURCE.zip'
    include = {'src', 'res', 'assets', 'tools', 'tests'}
    docs = {'AndroidManifest.xml', 'README.md', 'DECISIONS.md',
            'VERIFICATION_REPORT.md', 'requirements-build.txt', '.gitignore'}
    with zipfile.ZipFile(source, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(ROOT.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if rel.parts[0] not in include and str(rel) not in docs:
                continue
            if '__pycache__' in rel.parts or path.suffix.lower() in {'.jks', '.keystore', '.apk', '.idsig', '.pyc'}:
                continue
            archive.write(path, 'AutoTimelineSync-Android-Source/' + rel.as_posix())
        names = archive.namelist()
        if not any(n.endswith('src/com/naimat/autotimelinesync/MainActivity.java') for n in names):
            raise RuntimeError('Incomplete source archive')
        if any('signing-password' in n or n.endswith(('.jks', '.keystore')) for n in names):
            raise RuntimeError('Private signing data in archive')
    evidence = DELIVERY / 'Verification'
    for name in reports:
        dest = evidence / name
        dest.mkdir(parents=True, exist_ok=True)
        for f in (ROOT / 'Verification' / name).iterdir():
            if f.is_file() and f.suffix in {'.json', '.png'}:
                shutil.copy2(f, dest / f.name)
    sample = ROOT / 'Verification/API35/verified-export.mp4'
    shutil.copy2(sample, DELIVERY / 'Sample-Export-Test-Tones.mp4')
    probe = Path('D:/My Created Software/Final AutoTimelineSync-3.0.1-FINAL-PORTABLE/AutoTimelineSync/runtime/ffmpeg/ffprobe.exe')
    metadata = json.loads(subprocess.check_output([str(probe), '-v', 'error', '-show_entries',
        'stream=codec_name,width,height,r_frame_rate,duration,nb_frames,sample_rate,channels:stream_side_data=rotation:format=duration,size',
        '-of', 'json', str(sample)]))
    with zipfile.ZipFile(apk) as a:
        if not {'classes.dex', 'AndroidManifest.xml', 'resources.arsc'}.issubset(a.namelist()):
            raise RuntimeError('APK payload is incomplete')
    if sha(apk) != sha(DELIVERY / apk.name):
        raise RuntimeError('Delivered APK hash differs')
    release = dict(product='Auto Timeline Sync by Naimat', version='3.0.1 Android',
        package='com.naimat.autotimelinesync', min_android='8.0', target_api=35,
        apk_sha256=sha(apk), source_zip_sha256=sha(source),
        tests={k:dict(api=v['api'],count=v['count'],failures=v['failures']) for k,v in reports.items()},
        export=metadata, physical_phone_tested=False, windows_pixel_parity=False)
    (DELIVERY / 'RELEASE_RESULTS.json').write_text(json.dumps(release, indent=2), encoding='utf8')
    print(json.dumps(dict(folder=str(DELIVERY), apk_bytes=apk.stat().st_size,
        source_zip_bytes=source.stat().st_size, sha256=release['apk_sha256'], tests=release['tests']), indent=2))

if __name__ == '__main__':
    package()
