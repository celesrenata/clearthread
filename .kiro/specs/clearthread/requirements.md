# Requirements Document

## Introduction

ClearThread is a local-first desktop application that helps users privately analyze their own Facebook and Messenger data exports to reconstruct relationship histories, prepare context for therapy, recognize recurring interaction patterns, recover forgotten events, and understand how their own behavior and boundaries changed over time.

Central promise: Turn your message history into a private, evidence-backed relationship timeline and a therapy-ready account of what happened, what repeated, what helped, and how you changed.

ClearThread is NOT an abuse detector, AI therapist, diagnosis engine, partner-rating system, or social-media surveillance platform. The application organizes evidence, identifies explainable patterns, asks useful reflection questions, and leaves all interpretation and decisions under the user's control.

## Glossary

- **ClearThread**: The local-first desktop application described by this specification
- **User**: The individual adult who owns the Facebook account and voluntarily imports their own data
- **Source_Data_Vault**: The immutable storage layer that preserves original imported data unchanged
- **Normalized_Store**: The analytical storage layer containing source-independent canonical event records
- **Import_Pipeline**: The subsystem responsible for ingesting, validating, and normalizing Facebook/Messenger export data
- **Participant**: Any person identified in imported conversations, including the User
- **Conversation**: A message thread between two or more Participants
- **Relationship**: A named association between the User and one other Participant, with category and date metadata
- **Episode**: A contiguous or semantically connected sequence of messages about a meaningful topic
- **Episode_Engine**: The subsystem that proposes, classifies, and manages Episodes
- **Finding**: A pattern or observation derived from analysis, always linked to supporting evidence
- **Evidence_Reference**: A citation linking a Finding to specific source messages, episodes, or annotations
- **Relationship_Chapter**: An organized reconstruction of one Relationship including phases, events, and patterns
- **Therapy_Brief**: A user-configured export summarizing selected relationships, episodes, and patterns for therapy preparation
- **Pattern_Analyzer**: The subsystem that detects and presents interaction patterns from message data
- **Model_Provider**: An abstraction layer for local AI inference backends (Ollama, llama.cpp, MLX, etc.)
- **Analysis_Run**: A single execution of an analytical process, fully versioned and traceable
- **Provenance_Record**: Metadata tracking the origin, transformation, and derivation of every piece of data
- **Growth_Analyzer**: The subsystem that identifies positive patterns, resilience, and boundary improvement over time
- **Search_Engine**: The subsystem providing full-text and semantic search across the archive
- **Export_Engine**: The subsystem that generates Markdown, PDF, and JSON exports
- **Encryption_Layer**: The subsystem managing at-rest encryption, key management, and secure deletion
- **Data_Health_Report**: A summary of import completeness, quality issues, and data gaps
- **Reflection_Question**: A non-directive question generated to prompt user self-reflection
- **User_Annotation**: User-supplied context, corrections, or notes attached to any data object
- **Exclusion**: A user-defined rule removing specific people, conversations, or date ranges from analysis

## Requirements

---

### Requirement 1: Facebook Messenger JSON Import

**User Story:** As a User, I want to import my Facebook Messenger data export in JSON format, so that I can analyze my conversation history locally.

#### Acceptance Criteria

1. WHEN the User provides a ZIP archive containing Facebook Messenger JSON export data, THE Import_Pipeline SHALL extract and parse all message JSON files within the archive.
2. WHEN the User provides an extracted directory containing Facebook Messenger JSON export data, THE Import_Pipeline SHALL parse all message JSON files within the directory structure.
3. WHEN the User provides multiple export parts covering different date ranges, THE Import_Pipeline SHALL combine them into a unified import treating each as a separate import batch.
4. WHEN the Import_Pipeline encounters a JSON file with encoding problems or malformed Unicode, THE Import_Pipeline SHALL attempt recovery by interpreting raw bytes as Latin-1-encoded UTF-8 (the known Facebook export encoding quirk), re-encode to valid UTF-8, and record a parsing warning for each recovered record including the file path and byte offset of the issue.
5. WHEN the Import_Pipeline encounters a duplicate message (matching SHA-256 hash of sender, timestamp, and message content) across overlapping export files, THE Import_Pipeline SHALL retain one canonical copy and record the duplicate source references.
6. THE Import_Pipeline SHALL preserve attachment references (images, audio, video, GIFs, stickers) linking each attachment to its source message.
7. THE Import_Pipeline SHALL parse and store reactions, shared links, group conversation membership, participant changes, and nickname changes from the export data.
8. WHEN the Import_Pipeline encounters deleted-message markers or unsent-message placeholders, THE Import_Pipeline SHALL store them as message records with the appropriate deletion or unsent state.
9. THE Import_Pipeline SHALL normalize all timestamps to UTC, recording the original timezone information when available.
10. WHEN an import is interrupted before completion, THE Import_Pipeline SHALL persist progress state to disk and allow the User to resume from the last successfully processed file without reprocessing completed files.
11. THE Import_Pipeline SHALL stream large archives incrementally, maintaining a peak memory footprint no greater than 256 MB regardless of total archive size.
12. WHEN import processing completes, THE Import_Pipeline SHALL generate a Data_Health_Report summarizing: total messages parsed, conversations found, participants identified, attachments referenced, duplicates detected, encoding issues recovered, records with warnings, and date range covered.
13. IF the provided ZIP archive is corrupt, truncated, or cannot be read, THEN THE Import_Pipeline SHALL abort the import, report an error indicating which file could not be read, and preserve any records already successfully processed in that session.

---

### Requirement 2: Immutable Source Data Preservation

**User Story:** As a User, I want my original imported data preserved unchanged, so that I can always trace analysis results back to unmodified source material.

#### Acceptance Criteria

1. THE Source_Data_Vault SHALL store original imported records in an immutable layer that cannot be modified or deleted by any analytical operation, user-editing operation, or user-initiated delete operation.
2. THE Source_Data_Vault SHALL record for each imported record: import batch identifier, source file path, original record identifier, file content hash, individual record content hash, import timestamp, and parser version used.
3. IF any operation attempts to modify or delete an immutable source record, THEN THE Source_Data_Vault SHALL reject the operation and return an error indicating that source records are immutable.
4. WHEN the User requests re-analysis or re-import, THE Source_Data_Vault SHALL retain all previous import batches alongside new data indefinitely until the User explicitly invokes a purge operation on a specific batch.
5. THE Source_Data_Vault SHALL store transformation history documenting every processing step between source record and normalized record, including for each step: the step sequence number, operation name, input record reference, output record reference, and timestamp.
6. WHEN a parsing warning occurs during import, THE Source_Data_Vault SHALL associate the warning with the specific source record and preserve the original unparsed content.

---

### Requirement 3: Normalized Data Storage

**User Story:** As a User, I want my messages stored in a source-independent canonical format, so that analysis works consistently regardless of where data was imported from.

#### Acceptance Criteria

1. THE Normalized_Store SHALL represent each message with: internal ID, source ID, conversation ID, sender participant ID, recipient/participant IDs, original timestamp, normalized UTC timestamp, message text, message type (one of: text, media, sticker, link, system event, call, reaction-only, or unknown), attachment references, reactions, reply relationship, forwarded/quoted content indicator, deleted/unsent state, detected language, import provenance reference, content hash, owner-authored indicator, analysis eligibility flag (eligible or ineligible), and user exclusion state (included or excluded).
2. THE Normalized_Store SHALL maintain referential integrity between messages, conversations, participants, and attachments such that every foreign reference (conversation ID, participant ID, attachment reference) resolves to an existing record.
3. IF a normalized record references a conversation, participant, or attachment that does not exist in the Normalized_Store, THEN THE Normalized_Store SHALL reject the record and report a referential integrity error linking back to the source record.
4. WHEN a message is marked as owner-authored, THE Normalized_Store SHALL distinguish it from messages authored by other participants via query filtering, enabling retrieval of only owner-authored or only other-participant messages.
5. WHEN new messages are imported into the Normalized_Store, THE Normalized_Store SHALL index only the newly added or modified records without reprocessing records whose content hash has not changed.
6. THE Normalized_Store SHALL track content hashes for each message such that embedding, analysis, and indexing operations skip any message whose content hash matches the hash recorded in the most recent prior processing run.
7. WHEN the User changes a participant merge, exclusion setting, or relationship assignment, THE Normalized_Store SHALL update only the affected normalized records without requiring re-import from the Source_Data_Vault.

---

### Requirement 4: Participant Identity Management

**User Story:** As a User, I want to review and manage participant identities after import, so that I can correctly attribute messages and organize my relationships.

#### Acceptance Criteria

1. WHEN import completes, THE ClearThread SHALL present the User with a participant review interface listing all identified participants, displaying each participant's name and message count.
2. WHEN the User merges two or more participant identities, THE ClearThread SHALL combine their message histories under a single unified participant record and retain the original identifiers as aliases.
3. WHEN the User splits a participant identity, THE ClearThread SHALL require the User to reassign each message from the original identity to one of the resulting participant records before the split is finalized.
4. THE ClearThread SHALL require the User to confirm which participant identity represents themselves before any analysis proceeds, and SHALL prevent navigation to analysis features until this confirmation is made.
5. THE ClearThread SHALL allow the User to assign a display name of up to 100 characters and up to 10 aliases of up to 100 characters each to any participant.
6. THE ClearThread SHALL allow the User to categorize each relationship using one of the following: Partner, Former partner, Friend, Family, Coworker, Manager, Community member, Acquaintance, Unknown, or a custom category of up to 50 characters, with a maximum of 20 custom categories.
7. THE ClearThread SHALL allow the User to mark relationships as past or current and assign start and end dates at month-and-year granularity.
8. WHEN the User excludes a participant from analysis, THE ClearThread SHALL omit all messages involving that participant from subsequent analysis results and visually indicate the participant's excluded status in the participant list.
9. THE ClearThread SHALL NOT infer intimate or sexual relationship categories without explicit User confirmation.
10. THE ClearThread SHALL allow the User to add free-text notes of up to 2000 characters to any participant record.
11. THE ClearThread SHALL allow the User to return to the participant review interface and modify participant identities, categories, or exclusions at any time after initial setup.
12. IF the User attempts to merge or split participant identities after analysis has been performed, THEN THE ClearThread SHALL notify the User that affected analysis results will be recalculated and require confirmation before proceeding.

---

### Requirement 5: Full-Text and Semantic Search

**User Story:** As a User, I want to search across my entire message archive using both exact text and meaning-based queries, so that I can find relevant conversations and evidence.

#### Acceptance Criteria

1. WHEN the User enters a text query of at least 2 characters, THE Search_Engine SHALL return messages containing exact matches, ranked by a relevance score combining term frequency and recency, and display the first 50 results within 2 seconds.
2. WHEN the User enters a semantic query of at least 2 characters, THE Search_Engine SHALL return messages with a cosine similarity score of 0.7 or above using local embedding-based similarity search, ranked by descending similarity score, and display the first 50 results within 5 seconds.
3. THE Search_Engine SHALL support filtering results by: date range, participant, relationship, conversation, attachment presence, user-authored-only, episode type, annotation presence, and finding association, where multiple filters are combined using AND logic.
4. THE Search_Engine SHALL allow the User to save up to 100 search queries for repeated use, each identified by a user-provided name of up to 120 characters.
5. WHEN search results are displayed, THE Search_Engine SHALL provide a direct link from each result to the full source context showing at least 5 messages before and 5 messages after the matched message in the conversation.
6. THE Search_Engine SHALL operate entirely locally without sending queries or message content to external services.
7. IF a search query returns no matching messages, THEN THE Search_Engine SHALL display a message indicating no results were found and suggest broadening filters or modifying the query.
8. WHEN search results exceed 50 items, THE Search_Engine SHALL provide pagination controls allowing the User to navigate through additional pages of 50 results each.
9. IF the User submits an empty query or a query shorter than 2 characters, THEN THE Search_Engine SHALL display a message indicating the minimum query length requirement without executing the search.

---

### Requirement 6: Episode Detection and Review

**User Story:** As a User, I want the system to propose meaningful conversational episodes from my message history, so that I can review and organize important events without reading every message.

#### Acceptance Criteria

1. THE Episode_Engine SHALL propose episodes by combining: time-gap analysis, thread/reply structure, semantic clustering, entity and topic continuity, and optional local language-model classification.
2. THE Episode_Engine SHALL detect episodes involving: conflict, boundary setting, emotional support, practical support, requests, refusals, apologies, repair attempts, reconciliation, breakups, financial discussions, health events, grief, work stress, major decisions, positive celebrations, acts of care, growth moments, and user-defined topic categories.
3. WHEN the Episode_Engine proposes an episode, THE Episode_Engine SHALL include a minimum of 3 and a maximum of 10 surrounding context messages on each boundary of the episode to preserve conversational meaning.
4. THE ClearThread SHALL present proposed episodes in a review inbox where the User can accept, reject, edit boundaries, reclassify, split, or merge episodes.
5. THE Episode_Engine SHALL NOT treat proposed episodes as confirmed findings until the User has reviewed them.
6. WHEN the User edits an episode boundary or classification, THE Episode_Engine SHALL record the correction and weight subsequent detection of similar patterns toward the corrected classification.
7. THE Episode_Engine SHALL link each proposed episode to the specific source messages and conversation that compose it.
8. WHEN the User defines a custom topic category, THE Episode_Engine SHALL use it for future episode classification.
9. THE Episode_Engine SHALL present no more than 20 unreviewed proposed episodes in the review inbox at one time, queuing additional proposals until the User processes existing ones.
10. WHEN the Episode_Engine proposes an episode, THE Episode_Engine SHALL assign a confidence score between 0.0 and 1.0, and SHALL only surface episodes with a confidence score of 0.5 or above to the review inbox.
11. IF the Episode_Engine detects no episodes within a conversation, THEN THE Episode_Engine SHALL not populate the review inbox and SHALL indicate to the User that no episodes were identified.

---

### Requirement 7: Relationship Timeline

**User Story:** As a User, I want to see a chronological timeline for each relationship showing key events and episodes, so that I can understand how the relationship developed over time.

#### Acceptance Criteria

1. THE ClearThread SHALL display a chronological timeline for each Relationship showing confirmed episodes, annotated events, and user-defined phases, ordered from oldest to newest by date.
2. THE ClearThread SHALL visually distinguish each timeline entry using a distinct labeled indicator for each category: documented facts, calculated patterns, AI-generated summaries, user-supplied context, and periods with missing or uncertain data.
3. WHEN the User selects a timeline entry that is associated with an episode or evidence, THE ClearThread SHALL navigate to that episode or evidence and display the surrounding entries within the same conversation or source.
4. IF the User selects a timeline entry that has no associated episode or evidence, THEN THE ClearThread SHALL display the entry's details inline without navigation.
5. THE ClearThread SHALL allow the User to add custom events or annotations to the timeline by providing at minimum a date and a title of up to 200 characters, with an optional description of up to 2000 characters.
6. THE ClearThread SHALL display periods of no contact or data gaps lasting 30 or more days as explicitly labeled uncertain periods on the timeline, distinguishable from periods containing entries.
7. THE ClearThread SHALL allow the User to define up to 20 relationship phases with a label of up to 100 characters and start and end date boundaries.
8. IF a User defines relationship phases with overlapping date boundaries, THEN THE ClearThread SHALL accept the overlapping phases and display all applicable phase labels for entries within the overlap.
9. WHEN the User adds, edits, or removes a custom event, phase, or annotation, THE ClearThread SHALL update the timeline to reflect the change without requiring a page reload.

---

### Requirement 8: Interaction Pattern Findings

**User Story:** As a User, I want to see evidence-linked pattern findings about communication dynamics in my relationships, so that I can recognize recurring behaviors and prepare for therapy discussions.

#### Acceptance Criteria

1. THE Pattern_Analyzer SHALL detect observable communication patterns including: initiation frequency, repair initiation, response-time changes, question/acknowledgment balance, topic redirection frequency, repeated unresolved concerns, repeated boundary requests, respect for refusal, apology frequency and specificity, commitment follow-through, behavior change after apology, escalation duration, conversation abandonment, reconciliation timing, emotional support reciprocity, and practical support reciprocity.
2. WHEN the Pattern_Analyzer identifies a pattern, THE Pattern_Analyzer SHALL present it as a Finding containing: a neutral title (maximum 80 characters), plain-language explanation, at least 3 supporting evidence references each linking to a specific message or exchange, counterexamples found, a confidence assessment expressed as one of "Strong," "Moderate," or "Preliminary" based on the ratio of supporting evidence to counterexamples and the observation period length, applicable time period with start and end dates, data limitations, and at least 2 reflection questions.
3. THE Pattern_Analyzer SHALL search for counterexamples that contradict each proposed pattern by reviewing all available conversation data within the applicable time period and including at least 1 counterexample in the Finding when one exists.
4. THE Pattern_Analyzer SHALL NOT assign motives, diagnose conditions, or score participants.
5. THE ClearThread SHALL allow the User to mark any Finding as inaccurate, add context, or reject it entirely.
6. WHEN the User rejects or corrects a Finding, THE ClearThread SHALL record the correction and not re-propose the same Finding without new evidence.
7. THE Pattern_Analyzer SHALL present patterns using neutral language (e.g., "Pattern proposed", "Worth reviewing", "Supporting evidence", "Possible interpretation") and SHALL NOT use language that assigns blame, implies intent, or characterizes a participant's personality.
8. IF fewer than 5 exchanges relevant to a pattern exist within the observation period, THEN THE Pattern_Analyzer SHALL either withhold the pattern or present it with an explicit "Not enough information" indicator and a confidence assessment of "Preliminary."
9. WHEN a relationship has fewer than 20 total analyzed messages, THE Pattern_Analyzer SHALL display a notice indicating that pattern detection requires additional conversation data and SHALL NOT generate Findings for that relationship.
10. IF new conversation data contradicts a previously presented Finding by introducing counterexamples that outnumber the original supporting evidence, THEN THE Pattern_Analyzer SHALL flag the Finding as "Under review" and recalculate the confidence assessment.

---

### Requirement 9: User Annotations and Corrections

**User Story:** As a User, I want to add my own context, correct errors, and annotate any piece of data, so that my personal knowledge enriches and corrects the automated analysis.

#### Acceptance Criteria

1. THE ClearThread SHALL allow the User to attach free-text annotations of up to 5,000 characters to any message, episode, finding, participant, relationship, or timeline entry.
2. THE ClearThread SHALL allow the User to mark any AI-generated content as inaccurate and provide a correction of up to 5,000 characters.
3. WHEN the User provides a correction, THE ClearThread SHALL preserve both the original AI output and the user correction, with the correction taking precedence in all displays and exports.
4. THE ClearThread SHALL allow the User to exclude specific messages, conversations, participants, or date ranges from all analysis, and SHALL allow the User to reverse any exclusion to restore the content to active analysis.
5. WHEN data is excluded by the User, THE ClearThread SHALL ensure excluded content does not appear in any analysis results, findings, exports, or search results.
6. WHEN re-analysis is performed, THE ClearThread SHALL preserve all user annotations and corrections, applying them to the new results where the original target still exists.
7. IF a re-analysis removes or restructures content that has user annotations or corrections, THEN THE ClearThread SHALL retain the orphaned annotations in a reviewable list and notify the User that unmatched annotations require reassignment.
8. WHEN the User requests permanent deletion of derived data (findings, episodes, summaries), THE ClearThread SHALL prompt the User for confirmation before deleting, SHALL preserve all source data, and SHALL complete the deletion within 5 seconds of confirmation.
9. IF the User cancels a permanent deletion confirmation, THEN THE ClearThread SHALL retain all data unchanged.

---

### Requirement 10: Therapy Session Brief Builder

**User Story:** As a User, I want to build customized therapy preparation documents from my analyzed data, so that I can bring organized evidence and reflection questions to therapy sessions.

#### Acceptance Criteria

1. THE ClearThread SHALL provide an interface for the User to select: date range, relationships, episodes, topics, whether message excerpts are included, participant name visibility, sensitive media exclusion, and detail level (summary, standard, or comprehensive) for the Therapy_Brief.
2. THE Therapy_Brief SHALL support inclusion of: events since previous session, emotional/relationship concerns, conflicts, boundaries attempted, support received, repair attempts, repeated patterns, positive changes, discussion questions, relevant excerpts, user annotations, and data limitations noting any gaps in imported data or analysis coverage for the selected period.
3. THE Therapy_Brief SHALL NOT contain diagnoses, treatment recommendations, or statements presenting AI output as professional advice.
4. THE Therapy_Brief SHALL include between 3 and 10 reflection questions derived from the topics, patterns, and conflicts present in the selected material.
5. THE Therapy_Brief SHALL label each content item with one of the following source categories: direct evidence from messages, calculated patterns, AI-generated summaries, or user-supplied context, using a persistent visual indicator distinguishable without reliance on color alone.
6. WHEN the User initiates export of the Therapy_Brief, THE Export_Engine SHALL export the Therapy_Brief in the User-selected format from: printable PDF, Markdown, structured JSON, or private in-app view.
7. THE Therapy_Brief SHALL include only user-selected material with no additional content added without User approval.
8. WHEN the User excludes participant names from the brief, THE Export_Engine SHALL replace all occurrences of each excluded name with a single consistent pseudonym or role label per participant, maintained across the entire document.
9. IF the User's selection criteria match no analyzed data, THEN THE ClearThread SHALL display a message indicating no matching data was found and suggest adjusting the date range or selected filters.
10. WHEN the User has assembled a Therapy_Brief, THE ClearThread SHALL present a preview allowing the User to review, edit, reorder, or remove any section before finalizing or exporting.

---

### Requirement 11: Growth and Resilience Analysis

**User Story:** As a User, I want to see evidence of my personal growth, successful coping strategies, and supportive relationships over time, so that I can recognize progress and identify what helped me.

#### Acceptance Criteria

1. THE Growth_Analyzer SHALL identify "Patterns That Protected Me" including: seeking support, establishing boundaries, leaving escalating conversations, recognizing concerning patterns, asking for help, maintaining independence, recovering hobbies or interests, reconnecting with friends, safety planning, trusting personal judgment, refusing pressure, and improving communication directness.
2. THE Growth_Analyzer SHALL identify "People Who Showed Up" including: contacts who checked in at least once per week over a period of 30 days or more, offered practical support, respected confidentiality, encouraged independence, helped in unsafe situations, celebrated progress, and remained supportive across at least 3 separate episodes or interactions.
3. THE Growth_Analyzer SHALL identify "Growth Across Time" by comparing the User's earlier behavior to later behavior within the same relationship or context, detecting measurable shifts such as: clearer boundary expression, shorter participation in destructive conflicts, more direct communication, better support-network use, less self-blame language, increased willingness to disengage, more specific expression of needs, more consistent follow-through, and healthier repair patterns, where each shift is established by comparing at least 2 instances from an earlier period against at least 2 instances from a later period separated by a minimum of 30 days.
4. WHEN the Growth_Analyzer presents a growth finding, THE Growth_Analyzer SHALL link it to specific evidence showing the change over time by citing at least one earlier-behavior instance and at least one later-behavior instance with their respective timestamps.
5. THE Growth_Analyzer SHALL present growth findings with the same evidence standards as other findings: neutral title, plain-language explanation, supporting evidence references, counterexamples found, confidence assessment, applicable time period, data limitations, and reflection questions.
6. IF the Growth_Analyzer cannot identify at least 2 earlier-behavior instances and 2 later-behavior instances for a proposed growth pattern, THEN THE Growth_Analyzer SHALL either withhold the finding or present it with an explicit "Not enough information" indicator and reduced confidence.
7. THE Growth_Analyzer SHALL actively search for counterexamples that contradict each proposed growth pattern, including instances where earlier positive behavior regressed or later behavior did not sustain improvement.

---

### Requirement 12: Local Model Integration

**User Story:** As a User, I want ClearThread to use local AI models for analysis without sending my data to external services, so that my private conversations remain on my device.

#### Acceptance Criteria

1. THE Model_Provider SHALL support at least one local inference backend (Ollama, llama.cpp, MLX, or OpenAI-compatible local endpoint) at initial release.
2. THE Model_Provider SHALL support configuring different models for different tasks: classification, embedding, reasoning, and summarization.
3. THE Model_Provider SHALL expose configuration for: context length (range: 512 to 131072 tokens), temperature (range: 0.0 to 2.0), structured-output schema, maximum evidence window size (range: 1 to 200 messages), parallelism (range: 1 to 32 concurrent requests), prompt version, and model version.
4. THE ClearThread SHALL NOT send message content or user data to any external network endpoint unless the User explicitly enables a remote model provider through a dedicated settings action requiring at least one confirming input.
5. WHEN a remote model provider is configured, THE ClearThread SHALL present a consent prompt identifying the remote endpoint and data types to be sent, require the User to confirm via an explicit opt-in action, and keep the remote option disabled by default.
6. THE Model_Provider SHALL produce validated structured data conforming to typed schemas before generating prose summaries.
7. WHEN model output fails schema validation or contains unsupported claims, THE Model_Provider SHALL reject the output, record the failure in an observable log accessible to the User, and return an error indication to the calling component within 5 seconds of detection.
8. THE Model_Provider SHALL NOT allow AI-generated citations that reference messages not supplied to the model in the evidence window.
9. IF the local inference backend becomes unreachable or fails to respond within 30 seconds, THEN THE Model_Provider SHALL return an error indication to the calling component and preserve the original user data unmodified.
10. IF a configuration value is set outside its permitted range, THEN THE Model_Provider SHALL reject the configuration change and indicate which parameter violated its bounds.

---

### Requirement 13: Provenance and Auditability

**User Story:** As a User, I want to trace every finding, summary, and derived data back to its source and the process that created it, so that I can trust the analysis and understand when results change.

#### Acceptance Criteria

1. THE ClearThread SHALL record for every derived object: analysis run ID, analysis type, model name and version, prompt version, parser version, source record references, retrieval query used, retrieved evidence IDs, generation timestamp, confidence assessment (a normalized score from 0.0 to 1.0), user review state (one of: unreviewed, confirmed, disputed, or corrected), user corrections, and references to superseded versions.
2. WHEN the User inspects a finding, THE ClearThread SHALL display the provenance chain showing the source messages, each processing step with its run ID and parameters, and the final output, within 2 seconds of the inspection request.
3. WHEN re-analysis produces results that differ from a previous run on the same source data, THE ClearThread SHALL preserve both versions, label each with its run ID and timestamp, and annotate the newer version with the category of change that caused the difference (model change, new data added, or prompt update).
4. THE ClearThread SHALL NOT overwrite previous analysis results without first persisting the prior version and recording the superseding run ID that caused the replacement.
5. WHEN the User switches models or prompt versions, THE ClearThread SHALL label each finding with the model name, model version, and prompt version that produced it, so that findings from different configurations are visually distinguishable in any list or detail view.
6. THE ClearThread SHALL record the specific messages and evidence supplied to the model for each finding, enabling the User to verify that citations reference real supplied content.
7. IF provenance metadata for a derived object is incomplete or cannot be retrieved, THEN THE ClearThread SHALL display the object with a visible indicator that provenance is unavailable and identify which metadata fields are missing.

---

### Requirement 14: Encrypted Local Storage

**User Story:** As a User, I want my data encrypted at rest with secure key management, so that my private conversations are protected even if my device is compromised.

#### Acceptance Criteria

1. THE Encryption_Layer SHALL encrypt all message content and derived analytical data at rest using application-level encryption with a minimum key length of 256 bits.
2. THE Encryption_Layer SHALL support an optional user passphrase (minimum 8 characters) for key derivation, in addition to OS credential storage.
3. THE Encryption_Layer SHALL integrate with OS credential storage (e.g., GNOME Keyring, KDE Wallet, macOS Keychain) for key management.
4. IF OS credential storage is unavailable, THEN THE Encryption_Layer SHALL prompt the User to provide a passphrase for key derivation and display a message indicating that OS credential storage could not be accessed.
5. THE ClearThread SHALL automatically lock the application after a configurable idle timeout period with a default of 5 minutes and a configurable range of 1 to 60 minutes.
6. WHILE the application is locked, THE ClearThread SHALL prevent access to message content, analytical data, and export functions until the User re-authenticates with their passphrase or OS credential.
7. THE ClearThread SHALL support secure deletion of derived indexes and analytical data when the User requests permanent deletion, where secure deletion overwrites the data region before unlinking the file from the filesystem.
8. IF the User provides an incorrect passphrase during unlock, THEN THE ClearThread SHALL display an error message indicating authentication failure and allow the User to retry up to 10 consecutive attempts before requiring a 60-second wait period.
9. THE ClearThread SHALL NOT store sensitive message content in application logs, crash reports, or diagnostic output.
10. THE ClearThread SHALL NOT include analytics SDKs, advertising SDKs, or telemetry in the application by default.
11. WHEN the User exports data, THE Export_Engine SHALL support optional passphrase-based encryption of the export file, requiring a passphrase of at least 8 characters.
12. THE ClearThread SHALL NOT display sensitive message content in OS notification previews.

---

### Requirement 15: Export Capabilities

**User Story:** As a User, I want to export selected analysis results in multiple formats, so that I can share relevant material with my therapist or keep records outside the application.

#### Acceptance Criteria

1. THE Export_Engine SHALL support export in Markdown, PDF formatted for standard paper sizes (A4 and Letter), and structured JSON formats.
2. THE Export_Engine SHALL include only user-selected material in exports with no additional content included without explicit User selection.
3. THE Export_Engine SHALL label each section of exported documents with a content-type header indicating one of: "Original Message" (direct evidence), "Calculated Pattern", "AI-Generated Summary", or "User Annotation".
4. WHEN exporting evidence, THE Export_Engine SHALL include: original message text, sender identity, timestamp, up to 5 surrounding messages as conversation context, and source provenance reference.
5. THE Export_Engine SHALL warn the User when an export would include other participants' names, contact details, or identifying information, and SHALL require explicit User confirmation before proceeding with such an export.
6. THE Export_Engine SHALL NOT claim that exports have automatic legal admissibility or court-ready status.
7. IF export generation fails, THEN THE Export_Engine SHALL display an error message indicating the failure reason and SHALL preserve the User's selection state so the export can be re-attempted without re-selecting material.
8. WHEN an export is initiated, THE Export_Engine SHALL complete the export within 30 seconds for exports containing up to 500 selected items, or display a progress indicator if processing exceeds 3 seconds.

---

### Requirement 16: User Interface Principles

**User Story:** As a User, I want a calm, private, and nonjudgmental interface, so that I can engage with sensitive material without feeling pressured or surveilled.

#### Acceptance Criteria

1. THE ClearThread SHALL provide the following views: Import dashboard, Data-health report, Participant review, Relationship library, Relationship timeline, Episode review inbox, Evidence reader, Pattern findings, Therapy brief builder, Growth and resilience view, Export center, and Privacy and model settings.
2. THE ClearThread SHALL use only hedged, non-alarmist language for analytical output labels, limited to the following approved phrases and close synonyms: "Pattern proposed", "Worth reviewing", "Supporting evidence", "Possible interpretation", "Add context", "Mark inaccurate", "Not enough information", "Counterexample found".
3. THE ClearThread SHALL NOT display: red or orange warning/danger color treatments for analytical findings, numeric scores presented as gamified progress, leaderboards, social sharing prompts, labels using superlatives or alarm words (e.g., "toxic", "abuser", "dangerous"), countdown timers or streak counters tied to engagement, or automatic push notifications about relationship danger.
4. THE ClearThread SHALL allow the User to leave any view via a single user action (e.g., back button, close, or navigation click) without intermediate confirmation dialogs, progress-loss warnings, or interstitial screens.
5. THE ClearThread SHALL NOT display streak counters, daily-login rewards, urgency countdowns, "you'll miss out" messaging, or notification badges designed to re-engage the User with unfinished analysis.
6. THE ClearThread SHALL display a numeric confidence percentage (0–100%) and a plain-language data-limitation statement (maximum 280 characters) within the same visible viewport region as each finding, without requiring scrolling or expanding a collapsed section to view them.

---

### Requirement 17: Accessibility and Trauma-Aware Interaction

**User Story:** As a User, I want controls that let me manage my exposure to difficult content, so that I can pace my engagement and protect my wellbeing during analysis.

#### Acceptance Criteria

1. THE ClearThread SHALL allow the User to hide message previews in list views and search results.
2. THE ClearThread SHALL allow the User to blur or hide sensitive media (images, videos) by default, requiring an explicit per-item tap or click to reveal each piece of media.
3. WHEN the User pauses or cancels a running analysis, THE ClearThread SHALL stop processing within 2 seconds and preserve any partial results generated up to that point for later resumption.
4. THE ClearThread SHALL allow the User to skip specific relationships or conversations during guided workflows, and SHALL allow the User to return to skipped items from the workflow overview at any time.
5. WHEN the User marks an episode as "too difficult," THE ClearThread SHALL defer that episode and surface it in a dedicated "Deferred Reviews" list accessible from the main navigation, allowing the User to revisit it at a later time.
6. THE ClearThread SHALL allow the User to configure the maximum number of message excerpts shown in any single finding or summary, with a configurable range of 1 to 20 excerpts and a default value of 3.
7. THE ClearThread SHALL allow the User to disable automatic surfacing of content flagged by the system as distressing, requiring manual navigation to access it.
8. THE ClearThread SHALL allow the User to add personal grounding notes of up to 500 characters, visible in any sensitive view.
9. THE ClearThread SHALL NOT display message content, media thumbnails, or relationship names in OS notification previews or window titles visible to other applications.
10. WHEN a new User account is created, THE ClearThread SHALL enable all content-protection defaults (media blurring, hidden message previews, and notification redaction) so that the User must opt out of protections rather than opt in.

---

### Requirement 18: Speaker Attribution Integrity

**User Story:** As a User, I want correct attribution of who said what, so that analysis never confuses my words with another person's words.

#### Acceptance Criteria

1. THE Import_Pipeline SHALL preserve the original sender identity for every message as recorded in the source export, storing the sender identifier as an exact match to the value in the source file.
2. THE ClearThread SHALL NOT summarize, train on, or attribute another participant's words as if the User authored them.
3. WHEN displaying or exporting message content, THE ClearThread SHALL display the sender identity directly preceding or labeling the message text such that each message is unambiguously associated with exactly one sender.
4. WHEN the Episode_Engine or Pattern_Analyzer references message content, THE referenced content SHALL include sender attribution.
5. IF speaker attribution is missing from the source data, or if two or more participants share an identical display name within the same conversation, THEN THE Import_Pipeline SHALL flag the message with an attribution warning and exclude it from speaker-dependent analysis until the User confirms attribution.
6. IF sender identity for a previously attributed message becomes null or unresolvable during any processing stage, THEN THE ClearThread SHALL halt speaker-dependent analysis for that message and flag it with an attribution warning.

---

### Requirement 19: Data Exclusion and Privacy Controls

**User Story:** As a User, I want granular control over what data is included in analysis, so that I can protect my privacy and the privacy of others.

#### Acceptance Criteria

1. THE ClearThread SHALL allow the User to exclude specific participants from all analysis, making messages authored by those participants ineligible for analytical processes across all conversations (individual and group).
2. THE ClearThread SHALL allow the User to exclude specific conversations entirely, marking all messages within the conversation ineligible for analysis regardless of sender.
3. THE ClearThread SHALL allow the User to exclude specific date ranges from analysis, where any message with a normalized UTC timestamp falling within the specified range becomes ineligible.
4. THE ClearThread SHALL allow the User to remove individual messages from analysis eligibility.
5. WHEN data is excluded, THE ClearThread SHALL ensure no excluded content appears in: search results, episode proposals, pattern findings, exports, therapy briefs, growth analysis, or any other analytical output.
6. WHEN data is excluded, THE Source_Data_Vault SHALL retain the original data unchanged but the Normalized_Store SHALL mark it ineligible for analysis.
7. WHEN the User changes exclusion settings, THE ClearThread SHALL invalidate any existing findings, episodes, or summaries that reference newly-excluded content and flag them for reprocessing.
8. THE ClearThread SHALL allow the User to reverse a previous exclusion, restoring the affected data to analysis-eligible status.
9. WHEN the User initiates reprocessing after changing exclusion settings, THE ClearThread SHALL re-run affected analyses as background jobs, preserving user annotations and corrections per Requirement 9 criteria.
10. WHEN the User applies an exclusion that would invalidate existing findings, THE ClearThread SHALL display the count of affected findings and episodes before the User confirms the exclusion.

---

### Requirement 20: No Diagnosis or Person Scoring

**User Story:** As a User, I want assurance that the system will never diagnose conditions, score people, or tell me what to do about my relationships, so that I remain in control of all interpretation.

#### Acceptance Criteria

1. THE ClearThread SHALL NOT generate mental health diagnoses, personality disorder labels, or clinical assessments.
2. THE ClearThread SHALL NOT generate toxicity scores, abuse scores, danger ratings, or numeric person rankings.
3. THE ClearThread SHALL NOT advise the User to end or continue any relationship.
4. THE ClearThread SHALL NOT use language that frames AI-generated analysis as a professional recommendation, including phrasing such as "you should seek therapy," "this constitutes abuse," or "a therapist would say."
5. THE ClearThread SHALL NOT predict future behavior of any participant, including statements of the form "they will likely" or "this person is going to."
6. WHEN presenting pattern findings, THE Pattern_Analyzer SHALL describe observable communication patterns without attributing intent or motive to participants.
7. THE ClearThread SHALL present reflection questions rather than conclusions about relationship quality or participant character.
8. IF the User explicitly requests a diagnosis, person score, or directive relationship advice, THEN THE ClearThread SHALL decline the request and explain that it provides pattern observations only, not clinical or evaluative judgments.
9. WHEN the User asks a question that implies labeling a participant (e.g., "Is this person narcissistic?"), THE ClearThread SHALL respond by describing relevant observable communication patterns without applying the label.

---

### Requirement 21: Structured Output Validation

**User Story:** As a User, I want all AI analysis to be validated against defined schemas, so that findings are consistently structured and never contain hallucinated references.

#### Acceptance Criteria

1. THE Model_Provider SHALL require all AI analysis to produce validated structured data conforming to typed schemas before any prose is generated.
2. THE ClearThread SHALL define typed schemas for: episode proposal, pattern finding, evidence citation, reflection question, relationship chapter section, therapy brief section, confidence assessment, data limitation, and counterexample, where each schema specifies required fields, field types, and allowed value ranges.
3. WHEN model output fails schema validation, THE Model_Provider SHALL retry inference up to 3 attempts, and if all attempts fail, reject the output, log the failure, and not present invalid results to the User.
4. THE Model_Provider SHALL verify that all evidence references in model output correspond to messages actually supplied in the model's evidence window.
5. WHEN a model output references a message ID not present in the supplied evidence, THE Model_Provider SHALL reject that output as containing a hallucinated citation.
6. THE ClearThread SHALL record schema validation results as part of the Provenance_Record for each Analysis_Run, including: validation pass/fail status, number of attempts made, schema version used, fields that failed validation, and timestamp of validation.
7. IF the Model_Provider exhausts all retry attempts for an Analysis_Run without producing valid output, THEN THE ClearThread SHALL notify the User that analysis could not be completed, identify which analysis task failed, and allow the User to retry manually or adjust model configuration.

---

### Requirement 22: Performance and Scale

**User Story:** As a User, I want the application to handle large message archives efficiently, so that years of conversation history can be analyzed without excessive delays or resource exhaustion.

#### Acceptance Criteria

1. THE Import_Pipeline SHALL process archives containing up to 10 million messages using a streaming approach that keeps resident memory usage below 512 MB regardless of total archive size.
2. THE ClearThread SHALL support incremental analysis by selected relationship or date range, processing only messages matching the selected scope without requiring full-archive reprocessing.
3. THE ClearThread SHALL queue expensive analytical operations (embedding, model inference) as background jobs with progress indicators displaying percentage complete and number of items processed out of total items.
4. WHEN a background job is interrupted, THE ClearThread SHALL allow resumption from the last checkpoint without loss of completed work.
5. THE Normalized_Store SHALL return query results within 3 seconds when querying across up to 50,000 conversations and up to 1,000 participants.
6. THE Search_Engine SHALL return full-text search results within 2 seconds for archives up to 5 million messages.
7. THE ClearThread SHALL avoid re-embedding messages whose content hash has not changed since the last embedding run.
8. IF a background job fails to make progress for more than 5 minutes, THEN THE ClearThread SHALL mark the job as stalled and notify the user with an option to retry or cancel.

---

### Requirement 23: Misuse Prevention Design

**User Story:** As a User, I want confidence that the application is designed to resist misuse, so that it cannot easily be weaponized against others.

#### Acceptance Criteria

1. THE ClearThread SHALL require the User to confirm which participant identity represents themselves from the imported participant list before any analytical processing proceeds.
2. THE ClearThread SHALL constrain all analytical outputs (findings, summaries, patterns, relationship chapters) to describe the User's own experience, communication behavior, and growth, rather than producing evaluations, profiles, or characterizations of other participants as standalone outputs.
3. THE ClearThread SHALL NOT provide features designed for: analyzing a partner's account without their knowledge, secretly monitoring another person, evaluating employees, screening tenants, investigating dates, or conducting background checks.
4. WHEN generating findings or summaries, THE ClearThread SHALL use User-perspective framing ("how interactions unfolded", "whether concerns were resolved", "how User responded", "what User experienced") and SHALL NOT produce findings framed as assessments of another participant's character, personality, or intent.
5. THE ClearThread SHALL NOT support real-time or automated import from live accounts—only manual import of downloaded exports.
6. THE ClearThread SHALL NOT allow importing data from multiple distinct Facebook accounts simultaneously; each ClearThread instance SHALL analyze only one User's exported data.
7. THE ClearThread SHALL NOT generate standalone reports, profiles, or dossiers about other participants that could be extracted and used independently of the User's own relationship analysis.

---

### Requirement 24: Evidence Distinction

**User Story:** As a User, I want to always know whether I am looking at direct evidence, a calculated pattern, or an AI-generated interpretation, so that I can make informed judgments.

#### Acceptance Criteria

1. THE ClearThread SHALL display a distinct visual indicator (such as a label, icon, or dedicated styling) for each of the following content categories in all views and exports: documented facts (direct message evidence), calculated patterns (statistical analysis), AI-generated summaries, user-supplied context (annotations), and areas of uncertainty or missing data.
2. WHEN the ClearThread displays a summary or finding, THE ClearThread SHALL provide access to the underlying source evidence within one user interaction (e.g., a single click or tap).
3. THE ClearThread SHALL display a confidence assessment using a defined scale (e.g., high, medium, low) for all AI-generated content, where each level corresponds to documented criteria.
4. WHEN evidence is insufficient or contradictory, THE ClearThread SHALL display an explicit uncertainty indicator on the affected content rather than presenting best-guess interpretations as established facts.
5. THE ClearThread SHALL label the source type (direct quote, paraphrase, statistical calculation, model inference) for every claim in relationship chapters and therapy briefs.
6. IF the underlying source evidence for a summary or finding is no longer available, THEN THE ClearThread SHALL indicate that the source is unavailable rather than silently omitting the link.

---

### Requirement 25: Relationship Chapter Reconstruction

**User Story:** As a User, I want organized narrative reconstructions of individual relationships, so that I can understand the full arc of how a relationship developed, changed, and ended.

#### Acceptance Criteria

1. THE ClearThread SHALL generate a Relationship_Chapter for each user-selected Relationship, organized chronologically and including: date range, how the relationship began, major phases, important events, positive interactions, support given and received, recurring conflicts, boundary discussions, repair attempts, reconciliations, turning points, periods of contact and no-contact, ending (if applicable), post-relationship contact, and user reflections.
2. THE Relationship_Chapter SHALL cite at least one specific source episode for every prose claim, with citations linked to the originating episode by date and title.
3. THE Relationship_Chapter SHALL visibly mark each section as: documented fact, calculated pattern, AI-generated summary, user-supplied context, or uncertain/missing period.
4. WHEN evidence is contradictory or missing for a time period, THE Relationship_Chapter SHALL explicitly state what is unknown and identify the time range of the gap rather than filling gaps with speculation.
5. THE ClearThread SHALL allow the User to edit, annotate, reject sections of, or entirely regenerate any Relationship_Chapter, and SHALL persist all user edits such that they survive regeneration of unedited sections.
6. THE Relationship_Chapter SHALL include at least one identified positive pattern and at least one identified negative pattern when both exist in source data, ensuring neither category comprises more than 80% of the total patterns identified.
7. IF the selected Relationship has fewer than 3 source episodes available, THEN THE ClearThread SHALL inform the User that insufficient data exists for a full chapter reconstruction and SHALL offer to generate a partial summary instead.

---

### Requirement 26: Reflection Question Generation

**User Story:** As a User, I want the system to generate thought-provoking reflection questions based on my data, so that I can explore my own interpretations without being told what to think.

#### Acceptance Criteria

1. WHEN the ClearThread presents a Finding, episode, or pattern, THE ClearThread SHALL offer between 1 and 5 non-directive reflection questions that reference specific data elements from the presented Finding, episode, or pattern.
2. THE ClearThread SHALL frame reflection questions as open-ended inquiries that do not presume an answer or imply judgment.
3. THE ClearThread SHALL NOT frame reflection questions as leading questions that push the User toward a specific conclusion about a participant or relationship.
4. THE ClearThread SHALL allow the User to save their reflections as User_Annotations associated with the specific Finding, episode, or pattern that prompted the question.
5. THE ClearThread SHALL generate reflection questions using the local model with the same provenance tracking as other AI-generated content.
6. THE ClearThread SHALL allow the User to dismiss individual reflection questions or disable automatic reflection question generation entirely.

---

### Requirement 27: Background Job Management

**User Story:** As a User, I want visibility and control over long-running analysis operations, so that I can continue using the application while processing occurs and manage resource usage.

#### Acceptance Criteria

1. THE ClearThread SHALL execute expensive operations (import, embedding, model inference, re-analysis) as background jobs such that the user interface remains responsive to user input within 200 milliseconds while any background job is running.
2. THE ClearThread SHALL display progress indicators for all running background jobs, updated at least every 5 seconds, including: operation type, percentage complete, estimated time remaining, and current stage.
3. WHEN the User requests to pause, resume, or cancel a background job, THE ClearThread SHALL acknowledge the request within 3 seconds and transition the job to the corresponding state (paused, running, or cancelled).
4. WHEN the User cancels a background job, THE ClearThread SHALL preserve any work completed prior to cancellation and indicate how much of the operation was completed.
5. WHEN a background job fails, THE ClearThread SHALL display an error notification indicating the error type, the affected operation, and the stage at which failure occurred, preserve all work completed prior to the failure, and offer the User an option to retry from the failure point.
6. THE ClearThread SHALL allow the User to configure the maximum number of concurrent background jobs, with a default of 1 concurrent job, configurable from 1 to 8.
7. WHEN the number of requested background jobs exceeds the configured concurrency limit, THE ClearThread SHALL queue excess jobs and display their position in the queue.

---

### Requirement 28: Data Model Extensibility

**User Story:** As a User, I want the data model designed for future data sources beyond Facebook Messenger, so that I can eventually import conversations from other platforms.

#### Acceptance Criteria

1. THE Normalized_Store SHALL use a source-independent internal event model that does not embed Facebook-specific structures in the canonical schema.
2. THE Import_Pipeline SHALL use a plugin-based architecture where each data source has an independent importer that converts source-specific formats into the canonical model.
3. THE ClearThread SHALL preserve the source-platform identifier for each imported record while storing it in the universal schema.
4. WHEN a new importer is added in a future release, THE Normalized_Store SHALL accept its output without schema changes to the core analytical layer.

---

## Post-MVP Requirements

The following requirements are planned for future releases and are NOT in scope for the initial release. They are documented here for architectural awareness.

---

### Requirement 29: Post and Engagement Analytics (Post-MVP)

**User Story:** As a User, I want to analyze my Facebook posts and engagement patterns, so that I can understand how my public communication changed over time.

#### Acceptance Criteria

1. WHEN Facebook post export data is imported, THE ClearThread SHALL analyze: posting frequency, topic changes over time, meaningful comments versus reactions, posts that generated private conversations, audience changes, recurring language, communication style evolution, and public versus private voice differences.
2. THE ClearThread SHALL identify posts associated with relationship chapters or life events.
3. THE ClearThread SHALL flag old content the User may want to review for privacy or oversharing risks.
4. THE ClearThread SHALL present post analytics with the same evidence-linking and provenance standards as message analysis.

---

### Requirement 30: Relationship Safety Review (Post-MVP)

**User Story:** As a User, I want an optional mode that reviews patterns associated with controlling or harmful relationships, so that I can recognize concerning dynamics with professional guidance.

#### Acceptance Criteria

1. THE ClearThread SHALL require explicit User opt-in before enabling the safety review mode—it SHALL NOT activate automatically.
2. WHEN enabled, THE ClearThread SHALL review patterns involving: control, isolation, monitoring demands, financial pressure, threats, intimidation, humiliation, repeated boundary violation, sexual coercion, threats involving family/pets/property/self-harm, alternation between hostility and intense reconciliation, and escalation following expressions of independence.
3. THE ClearThread SHALL use neutral language in safety findings: "may be worth reviewing", "similar behaviors can occur in controlling relationships", "consider discussing with a professional".
4. THE ClearThread SHALL NOT conclude that abuse occurred solely from automated analysis.
5. THE ClearThread SHALL provide a fast way to leave sensitive safety-review views.
6. THE ClearThread SHALL store safety-resource information locally only (hotline numbers, support organizations).
7. THE ClearThread SHALL include guidance about risks of using the application on shared or monitored devices.
8. THE ClearThread SHALL support a configurable application lock separate from the standard idle timeout for safety-review content.

---

### Requirement 31: Evidence Export Packages (Post-MVP)

**User Story:** As a User, I want to create secure evidence packages of selected material with integrity verification, so that I can preserve a documented record for legal or personal purposes.

#### Acceptance Criteria

1. THE Export_Engine SHALL generate evidence packages containing: original messages with full context windows, timestamps, sender identities, attachment references, source file references, file and message content hashes, import metadata, user annotations (separate from source data), AI-generated summaries (clearly marked as derived), and a chain-of-custody-style manifest.
2. THE Export_Engine SHALL clearly distinguish original source material from AI-derived content within evidence packages.
3. THE Export_Engine SHALL NOT claim automatic court admissibility or legal standing for evidence packages.
4. THE Export_Engine SHALL warn the User when an evidence package would expose other participants' private information.
5. THE Export_Engine SHALL support optional encryption and password protection for evidence packages.

---

### Requirement 32: Cross-Relationship Pattern Book (Post-MVP)

**User Story:** As a User, I want to compare patterns across multiple relationships to understand my own growth and recurring behaviors, so that I can discuss evolving patterns with my therapist.

#### Acceptance Criteria

1. THE ClearThread SHALL allow the User to select two or more relationships for cross-comparison, focusing on the User's own behavior, needs, boundaries, and coping strategies.
2. THE ClearThread SHALL compare: how the User expressed concerns, responded to anger, apologized to end conflict, handled unresolved concerns, trusted over time, requested support, responded after saying no, withdrew from conflict, escalated, sought reassurance, sought outside support, recognized early warning signs, identified positive qualities, established stronger boundaries, and what helped the User leave or recover.
3. THE ClearThread SHALL identify growth and successful coping across relationships, not merely repeated harm.
4. THE ClearThread SHALL require User approval before including any relationship in cross-comparison analysis.
5. WHEN presenting cross-relationship comparisons, THE ClearThread SHALL apply the same evidence-linking, confidence, and provenance standards as single-relationship findings.

---

### Requirement 33: Privacy and Oversharing Audit (Post-MVP)

**User Story:** As a User, I want to scan my message history for accidentally exposed personal information, so that I can be aware of potential privacy risks.

#### Acceptance Criteria

1. THE ClearThread SHALL scan messages for potentially exposed: physical addresses, phone numbers, email addresses, birthdates, travel dates, workplace/school details, license plates, financial records, medical documents, security-question answers, identity documents, regular location patterns, and photos containing visible badges or paperwork.
2. THE ClearThread SHALL present detected exposures in a review queue for User assessment.
3. THE ClearThread SHALL NOT automatically delete or modify any content based on the audit—all decisions remain with the User.
4. THE ClearThread SHALL allow the User to dismiss audit findings as intentional or acceptable.

---

### Requirement 34: Reality Reconstruction (Post-MVP)

**User Story:** As a User, I want to organize evidence around disputed or confusing events, so that I can reconstruct what actually happened using timestamped records.

#### Acceptance Criteria

1. WHEN the User selects an issue or event for reality reconstruction, THE ClearThread SHALL organize: what each participant stated, earlier relevant messages providing context, commitments or agreements made, dates and timestamps, later references to the event, contemporaneous messages the User sent to friends or family about the event, user annotations, identified missing evidence, and conflicting evidence.
2. THE ClearThread SHALL present factual inconsistencies (e.g., contradictory statements, timeline conflicts) without assigning intent or motive.
3. THE ClearThread SHALL clearly indicate gaps where evidence is missing or conversations were excluded.
4. THE ClearThread SHALL support the "What Did I Know At The Time?" three-track view: Track A (what occurred—evidence from conversations), Track B (what User said at the time—messages to others during the same period), Track C (how User understands it now—current annotations and reflections).
5. THE ClearThread SHALL preserve the distinction between historical evidence and present-day interpretation in all reality-reconstruction views.

---

### Requirement 35: Testing and Quality Assurance

**User Story:** As a User, I want confidence that the application handles edge cases, adversarial inputs, and data corruption gracefully, so that analysis results are trustworthy.

#### Acceptance Criteria

1. THE ClearThread SHALL include automated tests for: incorrect speaker attribution, duplicate messages, out-of-order timestamps, partial exports, overlapping exports, missing participants, encoding corruption, very large conversations, interrupted imports, excluded messages leaking into analysis, excluded participants leaking into analysis, AI citations pointing to nonexistent messages, findings without supporting evidence, isolated excerpts without sufficient context, user corrections surviving re-analysis, and model changes altering conclusions without version history.
2. THE ClearThread SHALL include test fixtures simulating: healthy disagreement and repair, repeated unresolved concerns, clear boundary respect, repeated boundary disregard, emotional and mutual support, one-sided support, ambiguous conflict, sarcasm and jokes, quoted threats not made by the sender, fictional or role-play conversations, group-chat context shifts, multiple languages, missing context, and false-positive safety patterns.
3. THE ClearThread SHALL test that no sensitive data leaks into: application logs, crash reports, OS notifications, diagnostic bundles, or default telemetry.
4. THE ClearThread SHALL test resilience against: prompt injection attempts in imported messages, malicious attachments, corrupt ZIP archives, and extremely long messages.
5. WHEN a cloud model provider is disabled, THE ClearThread SHALL verify through automated testing that no data is transmitted to external endpoints.

---

### Requirement 36: Backup and Recovery

**User Story:** As a User, I want reliable backup and recovery of my data and analysis, so that I do not lose years of organized analysis due to hardware failure or corruption.

#### Acceptance Criteria

1. THE ClearThread SHALL support creating encrypted backups of: source data, normalized data, analysis results, user annotations, model configurations, and application settings.
2. THE ClearThread SHALL support restoring from a backup to a new installation while preserving all provenance records and user corrections.
3. WHEN restoring from backup, THE ClearThread SHALL verify data integrity using stored content hashes.
4. IF backup integrity verification fails, THEN THE ClearThread SHALL report which specific records are affected and allow partial restoration of valid data.
5. THE ClearThread SHALL support configuring automatic backup schedules to a user-specified local directory or network path.

---
