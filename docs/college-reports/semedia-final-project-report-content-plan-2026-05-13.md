# Semedia Final Project Report Content Plan

**Source outline:** `NguyeThanhVinh-23IT313-Báo cáo đồ án cơ sở 4-OldReport.pdf`

**Report language:** English for the entire report, including headings, body text, figure captions, table titles, diagram labels, and use case specifications.

**Goal:** Create a new college final project report for the Semedia semantic media search project while following the old report's outline, section order, and presentation style as closely as possible.

**Important constraint:** Keep the old report's high-level structure exactly: front matter, `INTRODUCTION`, `Chapter 1. THEORECTICAL BASIC`, `Chapter 2. SYSTEM ANALYSIS AND DESIGN`, `Chapter 3. IMPLEMENTATION`, `CONCLUSION`, and `REFERENCE DOCUMENTS`.

---

## 1. Extracted Outline from the Old Report

### Front Matter

1. Cover page
2. Repeated project title page
3. `INSTRUCTOR'S COMMENT`
4. `ACKNOWLEDGEMENT`
5. `TABLE OF CONTENTS`
6. `LIST OF FIGURES`
7. `LIST OF ABBREVIATIONS`

### `INTRODUCTION`

1. `Reason for choosing this topic`
2. `Implementation plan`
3. `Report structure`

### `Chapter 1. THEORECTICAL BASIC`

1.1 `Next.js Framework & App Router Architecture`  
1.2 `Real-Time Communication (WebRTC & LiveKit)`  
1.3 `Collaborative Synchronization (CRDTs & Y.js)`  
1.4 `Database & ORM (MongoDB & Prisma)`  
1.5 `Authentication & Identity Management`

For the Semedia report, keep the same number of theoretical sections, but replace the technology topics with Semedia's applied technologies.

### `Chapter 2. SYSTEM ANALYSIS AND DESIGN`

2.1 `System Requirements`  
- 2.1.1 `Actors`  
- 2.1.2 `Functional Requirements`

2.2 `Use case Diagram`  
- 2.2.1 `System-level Use Case Diagram`  
- 2.2.2 `Detailed Use Case: Upload Media`  
- 2.2.3 `Detailed Use Case: Search by Text`  
- 2.2.4 `Detailed Use Case: Search by Image`  
- 2.2.5 `Detailed Use Case Specifications`

2.3 `Activity Diagrams`  
- 2.3.1 `Authenticate User Activity Diagram`  
- 2.3.2 `Join Room Activity Diagram`  
- 2.3.3 `Collaborate on Whiteboard Activity Diagram`  
- 2.3.4 `Take Personal Notes Activity Diagram`  
- 2.3.5 `View Session History Activity Diagram`

2.4 `Sequence Diagrams`  
- 2.4.1 `Authenticate User Sequence Diagram`  
- 2.4.2 `Join Room Sequence Diagram`  
- 2.4.3 `Collaborate on Whiteboard Sequence Diagram`  
- 2.4.4 `Take Personal Notes Sequence Diagram`  
- 2.4.5 `View Session History Sequence Diagram`

2.5 `State Diagrams`  
- 2.5.1 `Room Lifecycle`  
- 2.5.2 `Whiteboard Collaboration State`  
- 2.5.3 `Personal Notes State`

2.6 `Class Diagram`

### `Chapter 3. IMPLEMENTATION`

3.1 `General Interface`  
3.2 `User Interface`

### `CONCLUSION`

1. `Obtained Results / Achievements`
2. `Limitations and Future Development`

### `REFERENCE DOCUMENTS`

---

## 2. Proposed Semedia Report Content by Section

## Front Matter

### Cover page

Follow the old report's cover format:

- School/university name
- Faculty/department name
- Project/report title
- Student name and student ID
- Instructor name
- Course or project module name
- Academic year or submission date

Suggested title:

**SEMANTIC MEDIA SEARCH SYSTEM USING BLIP, CLIP, TF-IDF, AND HYBRID RETRIEVAL**

Use English consistently for the entire report.

### Repeated project title page

Repeat the project title and student/instructor information, following the old report's second-page pattern.

### `INSTRUCTOR'S COMMENT`

Keep this as a blank or mostly blank page for instructor evaluation and signature.

### `ACKNOWLEDGEMENT`

Write a short acknowledgement:

- Thank the instructor for guidance.
- Thank the faculty/school for providing the learning environment.
- Mention that the project helped apply knowledge about web development, AI, computer vision, data processing, and software architecture.

### `TABLE OF CONTENTS`

Generate automatically in Word after all headings are finalized.

### `LIST OF FIGURES`

Generate automatically in Word. Use figure numbering by chapter, for example:

- `Figure 1-1. Overall semantic media search pipeline`
- `Figure 2-1. System-level use case diagram`
- `Figure 3-1. Upload interface`

### `LIST OF ABBREVIATIONS`

Recommended abbreviations:

| Abbreviation | Meaning |
|---|---|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| BLIP | Bootstrapping Language-Image Pre-training |
| CLIP | Contrastive Language-Image Pre-training |
| CNN | Convolutional Neural Network |
| CRUD | Create, Read, Update, Delete |
| DB | Database |
| IDF | Inverse Document Frequency |
| JSON | JavaScript Object Notation |
| ML | Machine Learning |
| MRR | Mean Reciprocal Rank |
| NDCG | Normalized Discounted Cumulative Gain |
| ORM | Object-Relational Mapping |
| REST | Representational State Transfer |
| SQL | Structured Query Language |
| TF | Term Frequency |
| TF-IDF | Term Frequency-Inverse Document Frequency |
| UI | User Interface |
| UX | User Experience |

---

# INTRODUCTION

## 1. Reason for choosing this topic

Semantic search for images and videos is an important practical problem because digital media collections are growing rapidly in education, communication, entertainment, research, and business. In many cases, users do not remember the exact file name or folder location of a media file. Instead, they remember the content of the image, the scene in a video, or the general meaning of what they saw. Traditional search methods based only on file names, upload dates, or manually entered metadata are therefore often insufficient.

This challenge is even greater for video data because a single video may contain many different scenes, objects, and events. Searching an entire video as one unit can hide the specific segment that is actually relevant to the user's query. For this reason, a more intelligent system is needed to analyze media content automatically and support retrieval based on meaning.

Semedia was developed to address this problem by combining computer vision, natural language processing, and information retrieval techniques. The system processes uploaded images and videos, generates captions, extracts semantic embeddings, builds a TF-IDF keyword index, and returns ranked results for both text-based and image-based search. The topic is meaningful because it integrates theory and practice into a complete software system with real search, ranking, and evaluation workflows.

## 2. Implementation plan

Use the implementation schedule from the original project proposal's `Kế hoạch thực hiện` table, translated into English while preserving the original timeframes.

| Timeframe | Task |
|---|---|
| 23/02 – 01/03 | Research relevant technologies and models, including CLIP and TF-IDF. |
| 02/03 – 15/03 | Analyze requirements and design the system architecture. |
| 16/03 – 22/03 | Build the backend and basic API; design the database schema. |
| 23/03 – 29/03 | Develop the ReactJS frontend. |
| 30/03 – 05/04 | Implement media upload and management features. |
| 06/04 – 12/04 | Build the video frame extraction module. |
| 13/04 – 19/04 | Integrate the CLIP model for embedding generation. |
| 20/04 – 26/04 | Build the vector similarity search system. |
| 27/04 – 03/05 | Integrate BLIP for media caption generation. |
| 04/05 – 08/05 | Implement TF-IDF search and combine search results. |
| 09/05 – 11/05 | Test and optimize the system. |
| 12/05 – 14/05 | Finalize the report and submit the project. |

Note: The source proposal mentions a Django backend in this schedule. In the final Semedia report, describe the implemented backend as FastAPI where the current system is discussed, but preserve this table as the original implementation schedule unless the instructor requests a revised schedule.

## 3. Report structure

This report is organized into three main chapters in addition to the introduction, conclusion, and references. The `INTRODUCTION` presents the reason for choosing the topic, the implementation plan, and the structure of the report. `Chapter 1. THEORETICAL BASIC` introduces the core concepts and technologies used in the project, including semantic media search, scene detection, caption generation, embeddings, hybrid retrieval, and implementation technologies. `Chapter 2. SYSTEM ANALYSIS AND DESIGN` presents system requirements, actors, use cases, and design diagrams. `Chapter 3. IMPLEMENTATION` describes the general interface and the main user screens of the Semedia system. Finally, the `CONCLUSION` summarizes the achieved results, limitations, and future development directions, and `REFERENCE DOCUMENTS` lists the technical and project sources used during development.

---

# Chapter 1. THEORECTICAL BASIC

The old report has five theoretical sections. For Semedia, keep five sections, but write them at a moderate level of detail: enough to explain the concepts clearly, without turning Chapter 1 into a textbook-style survey. Each section should focus on concepts that are directly used in the implemented system.

## 1.1 Semantic Media Search and System Architecture

Semantic media search is the task of retrieving images or videos according to their visual meaning rather than relying only on file names or manually written metadata. In practice, this problem can be approached through several methods. Metadata-based search depends on external descriptions, keyword search matches textual content such as captions, vector search compares semantic embeddings, and hybrid search combines lexical and semantic evidence to improve result quality. Because images and videos do not naturally contain structured textual meaning, automatic content representation is necessary.

In Semedia, images are indexed directly as media items, while videos are divided into scenes so that each scene becomes a searchable unit. This design improves retrieval precision because users often want a specific moment in a video rather than the entire file. The overall system flow is as follows: the user uploads media, the gateway API stores the file and creates a media record, the media worker processes the file, captions and embeddings are generated, the keyword index is updated, the search API performs retrieval and ranking, and the frontend displays grouped and scored results.

Semedia uses a service-based architecture. The `gateway-api` handles public upload, media management, runtime endpoints, and search proxying. The `media-worker` performs scene detection, caption generation, and CLIP embedding extraction. The `search-api` is responsible for hybrid retrieval, ranking, and result preparation. The `frontend` provides the user interface, while the `shared` package contains common models, database logic, processing utilities, and search logic used across backend services.

Recommended figure:

`Figure 1-1. Overall architecture of the Semedia semantic media search system`

## 1.2 Video Scene Detection and PySceneDetect

Purpose: explain how video is converted into searchable scene-level data.

Include:

- Definition of video scene detection.
- Why scene-level indexing is better than treating a full video as one item.
- Basic idea of detecting visual changes between frames.
- Introduction to PySceneDetect and content-based scene detection.
- Role of OpenCV in reading video frames and extracting keyframes/thumbnails.
- How Semedia applies scene detection:
  - calculates video duration;
  - applies adaptive thresholds depending on video length;
  - detects scene boundaries;
  - extracts a representative keyframe near the middle of each scene;
  - stores scene start time, end time, scene index, keyframe path, caption, and embedding.
- Explain that this creates a bridge from raw video to searchable visual segments.

Recommended figure:

`Figure 1-2. Video processing pipeline from raw video to searchable scenes`

## 1.3 BLIP Captioning and CLIP Embeddings

Purpose: explain the two central AI models used to represent visual content.

### BLIP

Include:

- BLIP stands for Bootstrapping Language-Image Pre-training.
- BLIP is used for image captioning: generating natural-language descriptions from images.
- In Semedia, BLIP generates captions for:
  - uploaded images;
  - extracted video scene keyframes;
  - scene-level descriptions used for keyword search and display.
- Captions help convert visual content into text, making it searchable by natural-language queries.
- Semedia improves caption reliability through cleanup, normalization, batching, and retry for weak captions.

### CLIP

Include:

- CLIP stands for Contrastive Language-Image Pre-training.
- CLIP maps text and images into a shared embedding space.
- Text queries, image queries, uploaded images, and video keyframes can be compared using vector similarity.
- Cosine similarity is used to measure how close two embeddings are.
- In Semedia, CLIP supports:
  - text-to-image/video-scene search;
  - image-to-image/video-scene search;
  - semantic matching beyond exact keywords.

Recommended figure:

`Figure 1-3. BLIP and CLIP roles in media understanding and semantic retrieval`

## 1.4 TF-IDF, Hybrid Retrieval, Ranking, and Evaluation

Purpose: explain the information retrieval methods used after media processing.

### TF-IDF

Include:

- TF means Term Frequency: how often a term appears in a document.
- IDF means Inverse Document Frequency: how rare or informative a term is across the corpus.
- TF-IDF assigns higher weight to words that are important in a specific document but not common everywhere.
- In Semedia, captions from images and scenes form the text corpus for keyword retrieval.
- The system persists keyword index artifacts so the index can be loaded at startup and rebuilt when the media library changes.

### Hybrid retrieval

Include:

- Vector search is good at semantic similarity but can miss exact lexical intent.
- Keyword search is good at exact terms but may miss conceptual similarity.
- Hybrid retrieval combines both signals.
- Semedia uses weighted fusion between vector score and keyword score.

### Ranking, reranking, and diversity

Include:

- Normalized scores are returned in the range `[0, 1]`.
- Ranking combines vector and keyword evidence.
- Reranking boosts can improve results when captions strongly match the query.
- Diversity limits prevent one video from dominating the result list with too many scenes.
- Explanation fields help users understand why a result was returned.

### Evaluation

Include:

- Search quality should be measured, not judged only by manual inspection.
- Semedia uses a locked benchmark corpus and judged query set.
- Recommended metrics to describe:
  - Precision@10;
  - Recall@10;
  - MRR;
  - NDCG@10.

Recommended figure:

`Figure 1-4. Hybrid retrieval and ranking flow`

## 1.5 Implementation Technologies: FastAPI, React, Docker, PostgreSQL, and SQLAlchemy

Purpose: introduce the main software technologies used to build and run the system.

Include:

### FastAPI

- Used for backend services.
- Provides REST API endpoints for upload, media management, health checks, search proxying, and search service operations.
- Supports request validation and structured API responses.

### React, TypeScript, and Vite

- Used for the frontend user interface.
- Supports media upload, text search, image search, media browsing, detail view, and result explanation display.
- TypeScript improves reliability through static typing.
- Vite provides fast frontend development and build tooling.

### Docker and Docker Compose

- Used to package and run the full stack consistently.
- Helps run gateway API, media worker, search API, frontend, database, and test services in a reproducible environment.

### PostgreSQL and SQLAlchemy

- PostgreSQL stores persistent application data.
- SQLAlchemy maps Python classes to database tables.
- Main domain models include `MediaItem`, `VideoScene`, and `KeywordIndexArtifact`.

### Supporting technologies

- PyTorch and Hugging Face Transformers: run BLIP and CLIP models.
- scikit-learn: TF-IDF vectorization and keyword retrieval support.
- NumPy: vector operations and similarity calculations.
- PySceneDetect and OpenCV: video scene detection and keyframe extraction.
- pytest and Vitest: backend and frontend testing.

Recommended figure:

`Figure 1-5. Main technologies used in Semedia`

---

# Chapter 2. SYSTEM ANALYSIS AND DESIGN

## 2.1 System Requirements

### 2.1.1 Actors

Use only external human actors that directly interact with the system.

1. **User**
   - Uploads images and videos.
   - Searches by text or image.
   - Views media details and search results.
   - Deletes media.

2. **Admin (System Maintainer/Developer)**
   - Monitors service health and system status.
   - Runs benchmark evaluation.
   - Reviews search-quality reports and tuning results.
   - Maintains the system during development and testing.

For UML use case diagrams, only `User` and `Admin` should appear as actors. Internal services such as the media worker and search service should be described as internal system components in the text or shown as participants in sequence diagrams, not modeled as external actors.

### 2.1.2 Functional Requirements

Recommended requirement groups:

#### Upload and media management

- `REQ-1.1`: The system shall allow users to upload image and video files.
- `REQ-1.2`: The system shall store uploaded files and create corresponding media records.
- `REQ-1.3`: The system shall display media processing status.
- `REQ-1.4`: The system shall allow users to view and delete media items.

#### Media processing

- `REQ-2.1`: The system shall automatically process uploaded images and videos.
- `REQ-2.2`: The system shall detect video scenes and extract representative keyframes.
- `REQ-2.3`: The system shall generate captions for images and video scenes.
- `REQ-2.4`: The system shall generate CLIP embeddings for searchable visual content.
- `REQ-2.5`: The system shall update the keyword index after media changes.

#### Search

- `REQ-3.1`: The system shall support text-based and image-based search.
- `REQ-3.2`: The system shall combine vector retrieval and keyword retrieval for text search.
- `REQ-3.3`: The system shall rank and normalize search results.
- `REQ-3.4`: The system shall limit duplicate or overly repetitive video-scene results.
- `REQ-3.5`: The system shall return explanation fields for search results.

#### User interface

- `REQ-4.1`: The frontend shall provide a media upload interface.
- `REQ-4.2`: The frontend shall provide a media library interface.
- `REQ-4.3`: The frontend shall provide text and image search interfaces.
- `REQ-4.4`: The frontend shall display result score, caption, media type, and explanation.
- `REQ-4.5`: The frontend shall group scenes that belong to the same video.

#### Evaluation

- `REQ-5.1`: The project shall include a fixed benchmark corpus.
- `REQ-5.2`: The project shall include judged evaluation queries.
- `REQ-5.3`: The project shall support reporting search-quality metrics.

## 2.2 Use case Diagram

### 2.2.1 System-level Use Case Diagram

Actors: `User`, `Admin`

Use cases for `User`:

- Upload media
- View media library
- Search by text
- Search by image
- View media detail
- Delete media

Use cases for `Admin`:

- Monitor system status
- Run benchmark evaluation
- View search-quality report

Recommended figure:

`Figure 2-1. System-level use case diagram of Semedia`

### 2.2.2 Detailed Use Case: Upload Media

Replace the old `Manage Account` detailed use case with `Upload Media`.

Content:

- User selects an image or video file.
- Frontend sends the file to the gateway API.
- Gateway API validates media type and stores the file.
- Gateway API creates a `MediaItem` record.
- System starts background processing.
- User receives upload status.

Recommended figure:

`Figure 2-2. Detailed use case diagram for uploading media`

### 2.2.3 Detailed Use Case: Search by Text

Replace the old `Join Room` detailed use case with `Search by Text`.

Content:

- User enters a natural-language query.
- Frontend sends query to gateway API.
- Gateway API proxies search request to search API.
- Search API obtains text embedding and keyword candidates.
- Ranking service merges and reranks candidates.
- Frontend displays results with explanations.

Recommended figure:

`Figure 2-3. Detailed use case diagram for text search`

### 2.2.4 Detailed Use Case: Search by Image

Replace the old `View Sessions` detailed use case with `Search by Image`.

Content:

- User uploads or selects a query image.
- System generates an image embedding using CLIP.
- Search API compares the query embedding with stored media and scene embeddings.
- Results are ranked and returned to the frontend.

Recommended figure:

`Figure 2-4. Detailed use case diagram for image search`

### 2.2.5 Detailed Use Case Specifications

Use the same table style as the old report.

Recommended use case specification tables:

#### Use Case 1: Upload Media

| Field | Content |
|---|---|
| Use Case Name | Upload Media |
| Actor | User |
| Description | The user uploads an image or video to the system. |
| Preconditions | The user has access to the application and the selected file is supported. |
| Postconditions | A media record is created and processing is started. |
| Main Flow | 1. User opens upload interface. 2. User selects file. 3. Frontend sends file to gateway API. 4. Gateway stores file. 5. Gateway creates media record. 6. The system starts processing. 7. The UI displays upload status. |
| Alternative Flow | If the file type is unsupported, the system rejects the upload and shows an error message. |

#### Use Case 2: Search by Text

| Field | Content |
|---|---|
| Use Case Name | Search by Text |
| Actor | User |
| Description | The user searches media using a natural-language text query. |
| Preconditions | The system contains processed media. |
| Postconditions | Ranked search results are displayed. |
| Main Flow | 1. User enters query. 2. Frontend sends query to gateway API. 3. Gateway forwards the request to the search API. 4. The system creates a text embedding and retrieves vector and keyword candidates. 5. The system fuses scores and reranks results. 6. The frontend displays ranked results. |
| Alternative Flow | If no matching result exists, the frontend displays an empty result state. |

#### Use Case 3: Search by Image

| Field | Content |
|---|---|
| Use Case Name | Search by Image |
| Actor | User |
| Description | The user searches media using an example image. |
| Preconditions | The user provides a valid image query. |
| Postconditions | Visually similar or semantically related results are displayed. |
| Main Flow | 1. User selects query image. 2. Frontend uploads the query image. 3. The system generates a CLIP image embedding. 4. The system compares it with stored embeddings. 5. The system ranks the candidates. 6. The frontend displays result cards. |
| Alternative Flow | If the image cannot be processed, the system displays an error message. |

#### Use Case 4: View and Delete Media

| Field | Content |
|---|---|
| Use Case Name | View and Delete Media |
| Actor | User |
| Description | The user views media details or deletes a media item. |
| Preconditions | The media item exists in the system. |
| Postconditions | Details are displayed or the item is removed from the system. |
| Main Flow | 1. User opens a media item. 2. The system displays metadata, caption, scenes, and thumbnails. 3. The user may choose delete. 4. The system removes database records and stored files. 5. Search data is refreshed. |
| Alternative Flow | If deletion fails, the system keeps the media item and displays an error message. |

#### Use Case 5: Run Benchmark Evaluation

| Field | Content |
|---|---|
| Use Case Name | Run Benchmark Evaluation |
| Actor | Admin |
| Description | The admin runs the benchmark workflow to evaluate search quality. |
| Preconditions | The benchmark corpus and judged queries are available. |
| Postconditions | A search-quality report is generated for review. |
| Main Flow | 1. Admin starts the evaluation workflow. 2. The system runs benchmark queries against the current stack. 3. The system calculates evaluation metrics. 4. The system outputs a report for review. |
| Alternative Flow | If evaluation data is missing or the run fails, the system reports the error and no final report is produced. |

## 2.3 Activity Diagrams

Keep five activity diagrams, matching the old report's structure.

Diagram format rule: Activity diagrams should be created in PlantUML or StarUML so they follow standard UML notation and are easy to export into the final report.

### 2.3.1 Upload Media Activity Diagram

Flow:

1. User opens upload page.
2. User selects image or video.
3. Frontend validates basic file input.
4. Frontend sends upload request.
5. Gateway API stores file.
6. Gateway API creates `MediaItem`.
7. Gateway API triggers processing.
8. UI shows processing status.

Recommended figure:

`Figure 2-5. Upload media activity diagram`

### 2.3.2 Process Media Activity Diagram

Flow:

1. Worker receives media item.
2. System checks media type.
3. If image:
   - generate caption;
   - generate CLIP embedding;
   - update media item.
4. If video:
   - detect scenes;
   - extract keyframes;
   - generate captions for scenes;
   - generate embeddings for scenes;
   - update scene records.
5. Rebuild or update keyword index.
6. Mark media item as completed.
7. If error occurs, mark as failed.

Recommended figure:

`Figure 2-6. Automatic media processing activity diagram`

### 2.3.3 Search by Text Activity Diagram

Flow:

1. User enters text query.
2. Frontend sends search request.
3. Gateway API forwards request.
4. Search API generates text embedding.
5. System performs vector retrieval.
6. System performs TF-IDF keyword retrieval.
7. Ranking service merges candidates.
8. Ranking service applies reranking and diversity.
9. Frontend renders results.

Recommended figure:

`Figure 2-7. Text search activity diagram`

### 2.3.4 Search by Image Activity Diagram

Flow:

1. User selects query image.
2. Frontend sends image search request.
3. Search service generates image embedding.
4. System compares query embedding against stored embeddings.
5. Ranking service orders results.
6. Frontend renders similar media.

Recommended figure:

`Figure 2-8. Image search activity diagram`

### 2.3.5 View Media Detail and Delete Media Activity Diagram

Flow:

1. User opens media item.
2. System loads media details.
3. If video, system loads scene list.
4. User reviews metadata, caption, and scenes.
5. If user chooses delete, system requests confirmation.
6. Gateway deletes records and files.
7. Search data is refreshed.

Recommended figure:

`Figure 2-9. View and delete media activity diagram`

## 2.4 Sequence Diagrams

Keep five sequence diagrams.

Diagram format rule: Sequence diagrams should be drafted in Mermaid for faster iteration and easier text-based maintenance during report preparation.

### 2.4.1 Upload Media Sequence Diagram

Participants:

- User
- Frontend
- Gateway API
- Database
- Media Worker / Background Task

Main sequence:

1. User selects file.
2. Frontend sends upload request to Gateway API.
3. Gateway API saves file to storage.
4. Gateway API creates media record in database.
5. Gateway API triggers processing task.
6. Gateway API returns upload response to frontend.
7. Frontend displays queued/processing status.

Recommended figure:

`Figure 2-10. Upload media sequence diagram`

### 2.4.2 Process Media Sequence Diagram

Participants:

- Media Worker
- Shared Pipeline
- Video Service
- Caption Service / BLIP
- CLIP Service
- Database
- Keyword Index Service

Main sequence:

1. Media Worker starts processing media item.
2. Shared Pipeline checks media type.
3. For video, Video Service detects scenes and extracts keyframes.
4. Caption Service generates captions.
5. CLIP Service generates embeddings.
6. Database stores updated media and scene data.
7. Keyword Index Service rebuilds durable TF-IDF index.
8. Pipeline marks item as completed.

Recommended figure:

`Figure 2-11. Media processing sequence diagram`

### 2.4.3 Search by Text Sequence Diagram

Participants:

- User
- Frontend
- Gateway API
- Search API
- Media Worker or CLIP Service
- Search Service
- Ranking Service
- Database / Keyword Index

Main sequence:

1. User submits text query.
2. Frontend calls Gateway API.
3. Gateway API forwards request to Search API.
4. Search API obtains CLIP text embedding.
5. Search Service retrieves vector candidates from stored embeddings.
6. Search Service retrieves keyword candidates from TF-IDF index.
7. Ranking Service fuses scores and applies reranking/diversity.
8. Search API returns normalized results.
9. Frontend displays result cards.

Recommended figure:

`Figure 2-12. Text search sequence diagram`

### 2.4.4 Search by Image Sequence Diagram

Participants:

- User
- Frontend
- Gateway API
- Search API
- CLIP Service
- Search Service
- Ranking Service
- Database

Main sequence:

1. User uploads query image.
2. Frontend sends image search request.
3. Gateway API forwards request to Search API.
4. CLIP Service generates image embedding.
5. Search Service compares query embedding with stored embeddings.
6. Ranking Service ranks candidates.
7. Search API returns results.
8. Frontend displays matched media/scenes.

Recommended figure:

`Figure 2-13. Image search sequence diagram`

### 2.4.5 View Media Detail and Delete Media Sequence Diagram

Participants:

- User
- Frontend
- Gateway API
- Database
- Storage
- Keyword Index Service

Main sequence:

1. User opens media detail page.
2. Frontend requests media detail from Gateway API.
3. Gateway API loads media and scenes from database.
4. Gateway API returns metadata, captions, thumbnails, and scene data.
5. If user deletes media, frontend sends delete request.
6. Gateway API deletes database records and stored files.
7. Keyword Index Service refreshes search index.
8. Frontend updates media library.

Recommended figure:

`Figure 2-14. View and delete media sequence diagram`

## 2.5 State Diagrams

Keep three state diagrams like the old report.

Diagram format rule: State diagrams should be created in PlantUML or StarUML so they remain consistent with standard UML state modeling.

### 2.5.1 MediaItem Lifecycle

States:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- optional logical end state: `DELETED`

Transitions:

- Upload creates `PENDING`.
- Worker starts and changes status to `PROCESSING`.
- Successful processing changes status to `COMPLETED`.
- Processing error changes status to `FAILED`.
- User deletion removes the item.

Recommended figure:

`Figure 2-15. Media item lifecycle state diagram`

### 2.5.2 VideoScene Processing State

States:

- `Detected`
- `Keyframe Extracted`
- `Captioned`
- `Embedded`
- `Indexed`

Transitions:

- Scene detection creates detected scenes.
- Keyframe extraction creates representative images.
- BLIP creates captions.
- CLIP creates embeddings.
- TF-IDF index includes scene captions.

Recommended figure:

`Figure 2-16. Video scene processing state diagram`

### 2.5.3 Keyword Index Artifact Lifecycle

States:

- `Empty`
- `Built`
- `Loaded`
- `Stale`
- `Rebuilt`

Transitions:

- Initial corpus creates `Built` index.
- Search API startup loads the latest index.
- Media upload/delete makes index stale.
- Rebuild creates updated index artifact.

Recommended figure:

`Figure 2-17. Keyword index lifecycle state diagram`

## 2.6 Class Diagram

Focus on domain models instead of every API DTO.

Recommended classes:

### `MediaItem`

Important attributes:

- `id`
- `filename`
- `media_type`
- `storage_path`
- `status`
- `duration`
- `caption`
- `embedding`
- `uploaded_at`
- `updated_at`

### `VideoScene`

Important attributes:

- `id`
- `media_id`
- `scene_index`
- `start_time`
- `end_time`
- `keyframe_path`
- `thumbnail_path`
- `caption`
- `embedding`

### `KeywordIndexArtifact`

Important attributes:

- `id`
- `format_version`
- `payload`
- `built_at`
- `document_count`

### Relationships

- `MediaItem` has many `VideoScene` records.
- `VideoScene` belongs to one `MediaItem`.
- `KeywordIndexArtifact` stores search index data built from media and scene captions.

Recommended figure:

`Figure 2-18. Semedia class diagram`

---

# Chapter 3. IMPLEMENTATION

## 3.1 General Interface

Use this section to describe the overall UI structure before showing individual screens.

Include:

- The frontend is built with React, TypeScript, and Vite.
- The frontend communicates with `gateway-api` through REST endpoints.
- The UI supports:
  - media upload;
  - media library browsing;
  - text search;
  - image search;
  - grouped video-scene results;
  - media detail viewing;
  - media deletion.
- Search results include normalized score, vector score, keyword score, caption, media metadata, and explanation fields.
- Video results can show scene-level matches so users can find relevant parts of a video.

Recommended figure:

`Figure 3-1. General interface layout of Semedia`

## 3.2 User Interface

Follow the old report's style: show screenshots and explain each screen in short paragraphs.

Recommended screens:

### Dashboard / Media Library Interface

Content to describe:

- Shows uploaded media items.
- Displays media type, thumbnail, caption preview, and processing status.
- Helps users understand what content is available for search.

Recommended figure:

`Figure 3-2. Media library interface`

### Upload Interface

Content to describe:

- User selects image or video file.
- System sends upload request to backend.
- UI displays queued, processing, completed, or failed state.

Recommended figure:

`Figure 3-3. Upload media interface`

### Text Search Interface

Content to describe:

- User enters natural-language query.
- Search can match visual meaning through CLIP and caption keywords through TF-IDF.
- Results are displayed as ranked cards.

Recommended figure:

`Figure 3-4. Text search interface`

### Search Result Card Interface

Content to describe:

- Shows thumbnail or keyframe.
- Shows caption and metadata.
- Shows normalized score and explanation.
- May show vector and keyword contributions.

Recommended figure:

`Figure 3-5. Search result card with score explanation`

### Grouped Video Scenes Interface

Content to describe:

- Shows relevant video scenes instead of only the whole video.
- Groups scenes by parent video.
- Helps users identify the exact part of a video that matches the query.

Recommended figure:

`Figure 3-6. Grouped video scene results`

### Image Search Interface

Content to describe:

- User uploads a query image.
- System returns semantically or visually similar media.
- Useful when the user has an example image but does not know how to describe it precisely.

Recommended figure:

`Figure 3-7. Image search interface`

### Media Detail Interface

Content to describe:

- Shows full metadata.
- Shows generated caption.
- For videos, shows detected scenes and thumbnails.
- Allows user to inspect or delete the media item.

Recommended figure:

`Figure 3-8. Media detail interface`

---

# CONCLUSION

## 1. Obtained Results / Achievements

Include:

- Successfully built a semantic media search system for images and videos.
- Implemented media upload and management features.
- Implemented automatic image and video processing pipeline.
- Applied video scene detection to convert videos into searchable scenes.
- Integrated BLIP for automatic caption generation.
- Integrated CLIP for text/image embeddings and semantic similarity search.
- Built durable TF-IDF keyword retrieval from generated captions.
- Combined vector search and keyword search using hybrid ranking.
- Added reranking, score normalization, result explanation, and diversity control.
- Built a React frontend for upload, search, result browsing, and media detail viewing.
- Created benchmark/evaluation infrastructure with fixed corpus, judged queries, and quality metrics.

Emphasize that Semedia is not only a UI prototype, but a complete pipeline: media ingestion, AI processing, retrieval, ranking, interface, and evaluation.

## 2. Limitations and Future Development

Recommended limitations:

- Current vector retrieval is local and may not scale well for very large datasets.
- Keyword index rebuild may be expensive as the media library grows.
- Search quality depends on generated captions and model performance.
- Complex video actions or abstract events may still be hard to retrieve accurately.
- Evaluation currently focuses on the locked benchmark corpus and may not fully represent all real-world use cases.
- The system is suitable for prototype/research scale but would need additional optimization for production-scale deployment.

Recommended future development:

- Integrate a specialized vector database or approximate nearest neighbor index.
- Improve caption quality using stronger captioning or vision-language models.
- Add OCR for text appearing inside images and videos.
- Add object detection or action recognition for richer video understanding.
- Improve query preprocessing and query expansion.
- Add user feedback logging for search-quality tuning.
- Improve frontend UX for filtering, sorting, scene navigation, and result comparison.
- Expand evaluation datasets and include more image-query benchmarks.

---

# REFERENCE DOCUMENTS

Use two groups of references.

## Official technical documentation

Recommended references:

- FastAPI official documentation
- React official documentation
- Vite official documentation
- Docker official documentation
- PostgreSQL official documentation
- SQLAlchemy official documentation
- PySceneDetect official documentation
- OpenCV official documentation
- Hugging Face Transformers documentation
- BLIP model documentation or paper
- CLIP model documentation or paper
- scikit-learn TF-IDF documentation
- PyTorch official documentation

## Internal project references

Recommended references:

- `docs/plan.md`
- `docs/TASKS.md`
- `docs/metrics/search_quality_history.md`
- `docs/metrics/search_tuning_checklist.md`
- `docs/metrics/evaluation_benchmark_rubric.md`
- `docs/implementations/phase2-processing-indexing.md`
- `docs/implementations/phase4-caption-quality.md`
- `docs/implementations/phase6-ranking-explanations.md`
- `docs/implementations/codebase-audit-report-2026-05-12.md`

---

## 3. Formatting and Style Patterns to Preserve from the Old Report

Preserve:

- Two initial title/cover pages.
- Instructor comment page.
- Acknowledgement page.
- Table of contents.
- List of figures.
- List of abbreviations.
- Three main chapters.
- Conclusion with exactly two subsections.
- Reference documents section at the end.
- Figure numbering by chapter, such as `Figure 1-1`, `Figure 2-1`, `Figure 3-1`.
- Use case specification tables.
- Diagram-heavy Chapter 2.
- Screenshot-heavy Chapter 3.

Do not add unless required by the instructor:

- Abstract section.
- List of tables.
- Appendix.

Recommended correction:

- Preserve the structure of the old report, but fix spelling in headings. For example, use `THEORETICAL BASIC` instead of the misspelled `THEORECTICAL BASIC`, unless the instructor explicitly requires the old wording.

---

## 4. Recommended Diagram and Screenshot Checklist

### Chapter 1 figures

- `Figure 1-1. Overall architecture of the Semedia semantic media search system`
- `Figure 1-2. Video processing pipeline from raw video to searchable scenes`
- `Figure 1-3. BLIP and CLIP roles in media understanding and semantic retrieval`
- `Figure 1-4. Hybrid retrieval and ranking flow`
- `Figure 1-5. Main technologies used in Semedia`

### Chapter 2 diagrams

- `Figure 2-1. System-level use case diagram of Semedia`
- `Figure 2-2. Detailed use case diagram for uploading media`
- `Figure 2-3. Detailed use case diagram for text search`
- `Figure 2-4. Detailed use case diagram for image search`
- `Figure 2-5. Upload media activity diagram`
- `Figure 2-6. Automatic media processing activity diagram`
- `Figure 2-7. Text search activity diagram`
- `Figure 2-8. Image search activity diagram`
- `Figure 2-9. View and delete media activity diagram`
- `Figure 2-10. Upload media sequence diagram`
- `Figure 2-11. Media processing sequence diagram`
- `Figure 2-12. Text search sequence diagram`
- `Figure 2-13. Image search sequence diagram`
- `Figure 2-14. View and delete media sequence diagram`
- `Figure 2-15. Media item lifecycle state diagram`
- `Figure 2-16. Video scene processing state diagram`
- `Figure 2-17. Keyword index lifecycle state diagram`
- `Figure 2-18. Semedia class diagram`

### Chapter 3 screenshots

- `Figure 3-1. General interface layout of Semedia`
- `Figure 3-2. Media library interface`
- `Figure 3-3. Upload media interface`
- `Figure 3-4. Text search interface`
- `Figure 3-5. Search result card with score explanation`
- `Figure 3-6. Grouped video scene results`
- `Figure 3-7. Image search interface`
- `Figure 3-8. Media detail interface`

---

## 5. Next Writing Order

Recommended order for drafting the full report:

1. Confirm English as the report language and keep all headings, figures, tables, and diagrams in English.
2. Create the Word document skeleton using the old report's outline.
3. Draft `INTRODUCTION` at moderate length.
4. Draft `Chapter 1. THEORETICAL BASIC` at moderate length, focusing only on concepts directly used in Semedia.
5. Create Chapter 2 diagrams and use case tables, ensuring that the system-level use case model includes only `User` and `Admin`.
6. Capture Chapter 3 screenshots from the running Semedia frontend.
7. Draft `CONCLUSION`.
8. Add references.
9. Generate the table of contents and list of figures.
10. Proofread formatting, figure numbering, terminology, and abbreviation consistency.

Note for future drafting workflow:

Independent report sections can be drafted in parallel with multiple Sonnet or Haiku subagents, for example by assigning separate subagents to `INTRODUCTION`, `Chapter 1`, `Chapter 2 diagrams`, `Chapter 3 interface descriptions`, and `CONCLUSION`. This can speed up report preparation, but the final document should still be reviewed manually for terminology consistency, chapter flow, and formatting uniformity.
