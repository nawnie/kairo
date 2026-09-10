# Safety sandbox implementation protocol

Kairo does not currently have proof of unrestricted intelligence or unsafe
autonomy. Before any real-program or unsupervised experiment expands its
permissions, `kairo_safety.sandbox.run` must be supplied an independent
operating-system isolation receipt. Without that receipt it refuses to launch.

The helper provides defense in depth—an allow-listed executable, disposable
working root, scrubbed environment, timeout, captured output, and before/after
file manifests—but it explicitly does not pretend those controls alone block
network access, privilege changes, or child-process escape. The external
sandbox verifier must prove those properties first.
