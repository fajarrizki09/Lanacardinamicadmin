fn main() {
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(
        tauri_build::AppManifest::new().commands(&[
            "start_backend",
            "native_get_paths",
            "native_get_diagnostics",
            "native_get_process_status",
            "native_open_path",
            "native_reveal_path",
            "native_open_external_url",
            "native_open_invoice_file",
            "native_print_file",
        ]),
    ))
    .expect("failed to build Tauri application")
}
