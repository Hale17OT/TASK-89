

(1) Workstation Guest Switcher vs. Individual Session Timeouts
- **Question:** Does the "guest switcher" allow multiple concurrent sessions or act as a quick-swap profile for a single workstation?
- **My Understanding:** It was unclear if the switcher extends the session or if timeouts apply globally to the workstation.
- **Solution:** Treat the switcher as a UI-level profile toggle for a single authenticated staff user. The **15-minute idle timeout** applies to the primary session; if triggered, the system force-logs the workstation, wipes the "recent-patient" cache for all profiles, and requires a full re-authentication.

(2) Searching vs. Masking in the MPI
- **Question:** How can staff search for patients using identifiers (like SSNs) that are masked by default in the UI?
- **My Understanding:** Masking usually interferes with search functionality if not handled correctly at the database level.
- **Solution:** Perform server-side exact matches on **deterministic encryption ciphertext** or hashed identifiers. Masking is strictly a display constraint: the database searches unmasked/encrypted values, but the UI only renders the masked version in the results.

(3) The Scope of "Break-Glass" Access
- **Question:** Does "break-glass" access provide a one-time reveal or a persistent session-wide elevation?
- **My Understanding:** The duration and scope of emergency access need to be limited to prevent unintended data exposure.
- **Solution:** Implement **Record-Level Elevation**. Entering a justification unmasks data for that specific record only for the current view. Refreshing the page or navigating away reverts the data to a masked state, necessitating a new log entry for further access.

(4) Definition of "Originality Status" Logic
- **Question:** How is "originality" verified in an offline environment without access to global image registries?
- **My Understanding:** The system must rely on internal data to detect reposts or duplicates.
- **Solution:** Determine originality via **internal cryptographic hash matching**. If an incoming file hash matches an existing record in the local MySQL DB, it is flagged as "Reposted." If unique, it is "Original." "Disputed" status remains a manual override for Compliance Officers.

(5) Retroactive Consent Revocation
- **Question:** How does revoking consent affect data that has already been exported or printed?
- **My Understanding:** Revocation cannot physically recall data once it leaves the digital system.
- **Solution:** Revocation is strictly **forward-looking**. The system will block new exports, update the audit trail, and add a "Revoked" watermark to digital metadata. The UI will display a prominent warning: "Warning: Physical copies may still exist."

(6) Local Outbox and Browser File System Constraints
- **Question:** How can a React web app write to a local system "Outbox" folder given browser security sandboxing?
- **My Understanding:** Browsers cannot directly access local paths like `C:/Shared/Outbox`.
- **Solution:** Manage the "Outbox" as a **Django-controlled directory** on the server machine. The React UI interacts with this via an API, providing a "Download from Outbox" interface and triggering server-side shell commands to manage the local printer spooler.

(7) Tamper-Evident Chaining Implementation
- **Question:** How will the audit logs be structured to prove they haven't been modified?
- **My Understanding:** This requires a linked structure where each entry validates the integrity of the previous one.
- **Solution:** Each log row includes a `previous_hash` column. Django calculates the hash for new entries as $SHA\text{-}256(\text{current\_data} + \text{previous\_row\_hash})$. An Integrity Check tool will allow Admins to verify that the chain remains unbroken.


(8) The 30-Minute Auto-Close for Unpaid Orders
- **Question:** How is the 30-minute auto-close enforced in an offline environment without cloud-based triggers?
- **My Understanding:** The system needs a local background process to monitor order ages.
- **Solution:** Implement a **Celery Beat task** running on the local server. It will heartbeat every 60 seconds, querying MySQL for `unpaid` orders where `created_at < now() - 30 minutes` and transitioning them to a `voided` status automatically.

(9) Watermarking: Client-Side Preview vs. Server-Side Save
- **Question:** Where should watermarks be applied to ensure both performance and data integrity?
- **My Understanding:** Client-side watermarks are easily bypassed, while server-side processing is more secure but slower for UI feedback.
- **Solution:** Use React (Canvas) for **real-time UI previews**. Upon saving, the original file and parameters are sent to Django, which uses the **Pillow** library to permanently "burn" the watermark into the pixels before storage.

(10) Admin Action "Sudo-Mode" Logic
- **Question:** Does the password re-entry for Admin actions create a new session?
- **My Understanding:** High-stakes actions require an extra layer of validation without disrupting the overall workflow.
- **Solution:** Implement a **"Sudo-Mode" pattern**. Validating the password against the $Argon2$ hash grants a "high-privilege token" valid for a 5-minute window, allowing the Admin to perform specific protected actions like log purges or system overrides.

(11) Handling "Reposted with Citation" Logic
- **Question:** Is an "authorization record" for reposts a text field or a physical file?
- **My Understanding:** Text-only citations are insufficient for legal compliance in clinical environments.
- **Solution:** Enforce a **hard file-link requirement**. A "Reposted" status is blocked until the user uploads a physical authorization file (PDF/Image). The "Originality Status" remains "Incomplete" until both the citation and the file are present.

(12) Identification of Workstations for Throttling
- **Question:** How can we identify a specific "workstation" in a web app where IPs may be shared?
- **My Understanding:** Relying solely on IP addresses can be unreliable for strict per-terminal throttling.
- **Solution:** Use a combination of the **Client IP address** and a persistent **Workstation ID** stored in the browser's `localStorage`. The IP acts as a fallback throttler if the local cache is cleared.

(13) Audit Log Archival vs. Deletion
- **Question:** How are logs managed after 180 days to maintain performance while meeting 7-year retention rules?
- **My Understanding:** Active logs should be separated from historical archives to keep standard searches fast.
- **Solution:** Use **partitioned MySQL tables**. Data older than 180 days moves to `logs_archive`, which is hidden from standard staff views but accessible to Compliance Officers. A manual "Purge" requiring double-auth is the only deletion path after the 7-year mark.

(14) Compensating Entries for Accounting Errors
- **Question:** How are accounting errors corrected if the "Delete" permission is revoked?
- **My Understanding:** To maintain an immutable audit trail, errors must be offset rather than erased.
- **Solution:** Revoke the `DELETE` permission at the SQL level. Implement corrections as **Compensating Entries** (e.g., a -$50.00$ row to offset a +$50.00$ error), linked to the original record via a `parent_entry_id`.


(15) Infringement Reporting Screenshots
- **Question:** How can the portal capture screenshots in a browser-restricted environment?
- **My Understanding:** Browsers cannot capture the full desktop; they can only see their own window.
- **Solution:** Use the `html2canvas` library to capture the **Portal's current DOM** for the report. For any external infringement evidence, the system will require the officer to perform a manual file upload.

(16) Reconciliation File Format and Frequency
- **Question:** When and how are the daily accounting reconciliation files generated?
- **My Understanding:** Offline systems might be powered down during standard midnight triggers.
- **Solution:** Attempt auto-generation of a CSV and signed PDF at 11:59 PM. If the server is offline, a **catch-up trigger** will fire immediately upon the first login of the following morning to cover the previous 24-hour cycle.

(17) Multi-image Fingerprinting and Collisions
- **Question:** How do we prevent hash collisions for similar-looking clinical photos?
- **My Understanding:** Metadata differences shouldn't result in different "Originality" statuses for the same image.
- **Solution:** Calculate the $SHA\text{-}256$ hash based on **raw pixel data only**. By excluding metadata, we ensure the "Originality" check is purely data-driven and unaffected by different file names or timestamps on identical images.

(18) "Remember this Device" for 30 Days
- **Question:** How does "Remember this device" work with 15-minute idle timeouts in a high-security environment?
- **My Understanding:** This cannot bypass the password requirement due to medical data risks.
- **Solution:** The "Remember this Device" token (stored in a secure, HttpOnly cookie) will only **pre-fill the username** and flag the browser as "trusted." It will never bypass the password entry, maintaining the 15-minute idle-timeout security layer.

(19) Subscription Failure Badges and Retries
- **Question:** How does the system handle "Retries" for hardware failures like a printer jam?
- **My Understanding:** Software can retry generation, but it cannot fix physical hardware issues.
- **Solution:** Software-level failures (timeouts) will trigger automatic retries. Hardware-level failures (printer spooler errors) will mark the status as **"Stalled,"** requiring a staff member to manually click "Mark as Resolved" once the physical obstruction is cleared.

(20) Application-Managed AES-256 Key Rotation
- **Question:** How is the "Master Key" secured in an offline environment without cloud-based HSMs?
- **My Understanding:** The key must be protected from physical theft of the server hardware.
- **Solution:** Store the Master Key in a protected environment variable, encrypted by a **"Startup Password."** An Administrator must enter this password manually whenever the server reboots to decrypt the key into memory, ensuring data remains unreadable if the hard drive is stolen.