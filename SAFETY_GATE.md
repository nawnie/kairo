# Kairo safety gate

The current Kairo experiments are bounded symbolic model-learning runs. They
are not autonomous agents and have no authority to operate the host system.

Before any experiment is allowed to move from finite adapters toward
unsupervised real-program operation, all of these gates must pass:

1. Run only inside a disposable, explicitly named sandbox directory or
   container. Never use the user's live project, credentials, home directory,
   network, or deployment profile as the test target.
2. Permit only an allow-listed executable and input tree. Deny network access,
   arbitrary child-process creation, privilege changes, and writes outside the
   sandbox.
3. Snapshot the sandbox before and after each task. Record every file change,
   process, output, and resource limit; reject the result if any receipt is
   missing.
4. Keep the evaluator/oracle outside the learner-visible inputs. Require an
   independently implemented replay and artifact check, including negative
   fault-injection tests.
5. Require human review before increasing action scope, persistence, duration,
   permissions, or moving to a new domain. A passing benchmark never grants
   unsupervised authority by itself.

Until these gates are implemented and independently verified for a real
program test, Kairo remains in the bounded local research lane.
