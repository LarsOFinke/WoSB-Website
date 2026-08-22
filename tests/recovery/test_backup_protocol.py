from __future__ import annotations
import base64, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from infrastructure.scripts.backup.backup_enrollment_contract import REQUEST_KIND, RESPONSE_KIND, validate_request, validate_response
from infrastructure.scripts.backup.backup_set_manifest import create_manifest, validate_manifest

def sidecar(path: Path) -> None:
    Path(f"{path}.sha256").write_text(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")

def test_backup_set_is_bound_to_spring_flyway_preflight(tmp_path: Path) -> None:
    root=tmp_path/'infra'; db=root/'data/backups/postgres/rbf.dump'; files=root/'data/backups/files/files.tar.gz'; report=root/'data/backups/reports/preflight.json'; target=root/'data/backups/sets/set.json'
    for path in (db,files,report,target): path.parent.mkdir(parents=True,exist_ok=True)
    db.write_bytes(b'postgres-custom'); files.write_bytes(b'files'); sidecar(db); sidecar(files)
    metadata=Path(f'{db}.restore.json')
    metadata.write_text(json.dumps({'schema_version':2,'backup':{'filename':db.name,'size_bytes':db.stat().st_size,'sha256':hashlib.sha256(db.read_bytes()).hexdigest(),'consistency':'application-quiesced'},'application':{'version':'1.0.0','flyway_version':'1'}}))
    sidecar(metadata)
    report.write_text(json.dumps({'schema_version':2,'mode':'preflight','status':'passed','recoverable':True,'source_artifact':{'filename':db.name,'size_bytes':db.stat().st_size,'sha256':hashlib.sha256(db.read_bytes()).hexdigest()},'checks':[{'name':name,'status':'passed'} for name in ('dump_inventory','staging_database_restore','flyway_validation','application_readiness','preflight_cleanup')]}))
    sidecar(report)
    create_manifest(root,target,files=files,postgres=db,verification=report); sidecar(target)
    assert validate_manifest(root,target)['committed'] is True

def test_backup_set_accepts_shared_data_behind_a_versioned_release_symlink(tmp_path: Path) -> None:
    root=tmp_path/'rbf'; infra=root/'releases/1.0.3/infrastructure'; shared=root/'shared/data'; shared.mkdir(parents=True); infra.mkdir(parents=True)
    (infra/'data').symlink_to(shared, target_is_directory=True)
    files=infra/'data/backups/files/files.tar.gz'; target=infra/'data/backups/sets/set.json'
    files.parent.mkdir(parents=True); target.parent.mkdir(parents=True); files.write_bytes(b'files'); sidecar(files)
    create_manifest(root,target,files=files); sidecar(target)
    payload=validate_manifest(root,target)
    assert payload['artifacts']['files']['path']=='shared/data/backups/files/files.tar.gz'

def test_backup_enrollment_response_is_request_bound() -> None:
    provisioner=b'#!/usr/bin/env bash\nset -Eeuo pipefail\n'
    ingest=b'#!/usr/bin/env python3\n'
    request=validate_request({'schema_version':1,'kind':REQUEST_KIND,'enrollment_id':'A'*32,'ssh_public_key':'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeEnrollmentKey= rbf@host','requested_username':'rbf-backup','requested_directory':'/incoming','created_at':'2026-08-01T10:00:00+00:00','product_hostname':'rbf.example.net','release_version':'1.7.33','provisioner_base64':base64.b64encode(provisioner).decode(),'provisioner_sha256':hashlib.sha256(provisioner).hexdigest(),'ingest_script_base64':base64.b64encode(ingest).decode(),'ingest_script_sha256':hashlib.sha256(ingest).hexdigest()})
    response=validate_response({'schema_version':1,'kind':RESPONSE_KIND,'enrollment_id':request['enrollment_id'],'host':'backup.example.net','port':22,'username':'rbf-backup','remote_directory':'/incoming','receipt_directory':'/receipts','recovery_directory':'/data','host_key':'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=','host_key_fingerprint':'SHA256:'+'A'*43,'age_recipient':'age1'+'a'*58,'managed_server':True,'trust_model':'server-controlled-ingest-v1'},expected_enrollment_id=str(request['enrollment_id']))
    assert response['managed_server'] is True

def test_backup_enrollment_request_rejects_a_tampered_embedded_provisioner() -> None:
    provisioner=b'#!/usr/bin/env bash\n'
    ingest=b'#!/usr/bin/env python3\n'
    payload={'schema_version':1,'kind':REQUEST_KIND,'enrollment_id':'A'*32,'ssh_public_key':'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeEnrollmentKey= rbf@host','requested_username':'rbf-backup','requested_directory':'/incoming','release_version':'1.8.0','provisioner_base64':base64.b64encode(provisioner).decode(),'provisioner_sha256':'0'*64,'ingest_script_base64':base64.b64encode(ingest).decode(),'ingest_script_sha256':hashlib.sha256(ingest).hexdigest()}
    try:
        validate_request(payload)
    except ValueError as exc:
        assert 'checksum mismatch' in str(exc)
    else:
        raise AssertionError('tampered provisioner was accepted')

def test_managed_backup_server_reenrollment_reuses_recovery_keys_safely() -> None:
    provisioner = (ROOT / 'tools/backup-server/provision-rbf-backup-server.sh').read_text()
    state_check = provisioner.index('EXISTING_MANAGED=false')
    key_handling = provisioner.index('RECOVERY_KEY="$RECOVERY_DIR/rbf-recovery-readonly-ed25519"')
    assert state_check < key_handling
    assert 'Existing managed state does not match {key}.' in provisioner
    assert '[[ "$EXISTING_MANAGED" == true && -f "$RECOVERY_KEY" && ! -L "$RECOVERY_KEY"' in provisioner
    assert '[[ "$EXISTING_MANAGED" == true && -f "$AGE_IDENTITY" && ! -L "$AGE_IDENTITY" ]]' in provisioner
    assert 'AGE_RECIPIENT="$(age-keygen -y "$AGE_IDENTITY")"' in provisioner

def test_strategy_rows_and_backgrounds_remain_inside_full_recovery_scope() -> None:
    postgres_backup = (ROOT / 'infrastructure/scripts/backup/backup-postgres.sh').read_text()
    files_backup = (ROOT / 'infrastructure/scripts/backup/backup-data.sh').read_text()
    recovery_restore = (ROOT / 'infrastructure/scripts/backup/restore-recovery.sh').read_text()
    strategy_migration = (ROOT / 'spring-api/src/main/resources/db/migration/V10__strategy_planner.sql').read_text()

    assert 'CREATE TABLE strategy_plans' in strategy_migration
    assert 'background_file_id' in strategy_migration
    assert 'pg_dump --format=custom' in postgres_backup
    assert '--exclude-table' not in postgres_backup
    assert 'backup_paths=(uploads)' in files_backup
    assert 'restore-data.sh" --yes "$files"' in recovery_restore
    assert 'restore-postgres.sh" "$postgres"' in recovery_restore
