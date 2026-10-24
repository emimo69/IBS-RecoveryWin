# shellcheck shell=bash
# Root-only session setup, sourced by the two fixed pkexec entry points.
ibs_session_init() {
    [[ $EUID == 0 ]] || { echo "Avviare tramite il launcher e pkexec." >&2; exit 1; }
    [[ -n ${DISPLAY:-} && -n ${XAUTHORITY:-} && -r $XAUTHORITY ]] || {
        echo "Sessione grafica non disponibile: DISPLAY/XAUTHORITY mancanti. Usare il launcher XFCE con la policy IBS installata." >&2
        exit 1
    }
    case "$MODE" in uefi|legacy) ;; *) echo "Firmware non valido" >&2; exit 1 ;; esac
    /usr/local/sbin/ibs-qemu-preflight "$MODE" "$SESSION_KIND"
    DISK=$(/usr/local/sbin/ibs-disk-check "$DISK")
    # A persistent root-owned lock shared by protected and direct modes.
    install -d -m 0700 -o root -g root /run/ibs-qemu
    exec 9>"/run/ibs-qemu/$(lsblk -dnro MAJ:MIN "$DISK" | tr : _).lock"
    flock -n 9 || { echo "Disco già utilizzato da una sessione IBS QEMU." >&2; exit 1; }
    # Bind identity to the actual open device: rename/hotplug must fail closed.
    IDENTITY=$(lsblk -bdnro MAJ:MIN,SIZE,MODEL,SERIAL,WWN "$DISK")
}
ibs_revalidate() {
    /usr/local/sbin/ibs-disk-check "$DISK" >/dev/null
    [[ "$(lsblk -bdnro MAJ:MIN,SIZE,MODEL,SERIAL,WWN "$DISK")" == "$IDENTITY" ]] || {
        echo "L'identità del disco è cambiata. Selezionarlo nuovamente." >&2; exit 1;
    }
}
ibs_qemu_args() {
    ARGS=(-machine q35 -m 4096 -smp 2 -nic "user,model=e1000" -vga std)
    if [[ -r /dev/kvm && -w /dev/kvm ]]; then ARGS+=(-accel kvm); else ARGS+=(-accel tcg); fi
    if [[ "$MODE" == uefi ]]; then
        cp /usr/share/OVMF/OVMF_VARS_4M.fd "$WORKDIR/ovmf-vars.fd"
        ARGS+=(-drive "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd"
               -drive "if=pflash,format=raw,file=${WORKDIR//,/,,}/ovmf-vars.fd")
    fi
}
