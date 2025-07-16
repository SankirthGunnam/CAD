# Gitlike workflow in p4

# Perforce Git-like Branching Workflow Guide

This document outlines a recommended workflow for adopting Git-like branching semantics within a Perforce Helix Core environment. The goal is to provide a more structured and collaborative development process, similar to what teams experience with Git and platforms like GitHub, while leveraging Perforce's robust version control capabilities.

## 1. Introduction

Traditionally, Perforce workflows often involve a "mainline" or "stream" model where changes are integrated directly or through simple merges. This guide introduces a more explicit branching strategy, akin to Git's feature branching, to facilitate:

- **Isolated Development:** Work on features without impacting the main codebase.
- **Code Reviews:** Formalize the review process before merging changes.
- **Clear History:** Maintain a cleaner and more understandable project history.
- **Parallel Development:** Enable multiple teams/developers to work concurrently on different features.

## 2. Core Concepts: Git vs. Perforce Mapping

Let's clarify how common Git concepts translate to Perforce:

| Git Concept | Perforce Equivalent(s) | Description |
| --- | --- | --- |
| **Repository** | Depot | The central data store for all project files and history. |
| **Branch** | Branch (using `p4 populate`, `p4 integrate -b`, or Streams) | A separate line of development. We will primarily use `p4 populate` or `p4 integrate -b` for explicit "branching" from a source path to a target path. Perforce Streams offer a more integrated branching solution, but this guide focuses on a path-based approach for simplicity. |
| **Commit** | Changelist / Submit | A set of atomic changes (files, adds, edits, deletes) submitted to the depot. Each submit creates a new revision. |
| **Merge** | Integrate (`p4 integrate`, `p4 resolve`) | Combining changes from one branch (source) into another (target). Perforce handles merges through integration and subsequent resolution of conflicts. |
| **Pull Request** | Shelved Changelist + Review Process | A request to merge changes from a feature branch into a main branch, typically involving code review. In Perforce, this is mimicked by shelving changes and requesting a review. |
| **Clone** | Workspace (`p4 client`) | A local copy of the repository files, where you make changes before submitting them. |

## 3. Branching Strategy

We will adopt a simplified Gitflow-like model:

- **`//depot/project/main`**: The stable, production-ready codebase. Only release-ready code should reside here. Integrations from `develop` or `release` branches.
- **`//depot/project/develop`**: The main development branch. All new features are ultimately integrated here. This branch should always be deployable to a staging environment.
- **`//depot/project/features/<feature_name>`**: Short-lived branches for developing specific features. These are branched off `develop` and integrated back into `develop` upon completion and review.
- **`//depot/project/release/<version>`**: (Optional, for larger projects) Branches created from `develop` for preparing a new release. Bug fixes are applied here and then integrated back to `develop` and `main`.
- **`//depot/project/hotfixes/<hotfix_name>`**: (Optional) Branches created directly from `main` to address critical production bugs. Integrated back to `main` and `develop`.

**Visual Representation (Conceptual):**

```
main <--------------------------------------------------------------------
  ^                                                                      |
  | (release merge)                                                      | (hotfix merge)
  |                                                                      |
develop <-------------------------<--------------------------------------
  ^       ^                       ^
  |       | (feature merge)       | (feature merge)
  |       |                       |
  |       feature/A               feature/B
  |         ^                       ^
  |         | (branch from develop) | (branch from develop)
  |         |                       |
  +---------+-----------------------+

```

## 4. Workflow - Creating a Feature Branch

When starting a new feature, you will create a new branch from the `develop` branch.

**Prerequisites:**

- Ensure your workspace is synced to the latest `develop` (`//depot/project/develop/...`).

**Steps:**

1. **Sync to `develop`:**
    
    ```
    p4 client # Ensure your client view maps to //depot/project/develop/...
    p4 sync //depot/project/develop/...
    
    ```
    
2. **Create the Feature Branch Directory:**
On the Perforce server, you'll need to create the target directory for your new branch. This is typically done by adding a new folder to the depot.
    
    ```
    # Example: Create a new changelist
    p4 change -o
    # Edit the changelist description, then save and exit.
    # Add the new directory path to the changelist description.
    # For instance, if your feature branch will be //depot/project/features/my-new-feature
    # You might not need to explicitly 'add' a directory if p4 populate creates it.
    # However, ensure the parent directory //depot/project/features exists.
    
    ```
    
3. **Populate the Feature Branch:**
Use `p4 populate` to copy the files from `develop` to your new feature branch path. This creates a new branch history.
    
    ```
    p4 populate //depot/project/develop/... //depot/project/features/my-new-feature/...
    
    ```
    
    - Replace `my-new-feature` with a descriptive name for your feature.
    - This command creates a pending changelist with the copied files.
    - **Important:** Review the changelist description and submit it. This submit officially creates your branch.
    
    Alternatively, if you have a branch specification defined (more advanced), you could use `p4 integrate -b <branch_spec_name>` followed by `p4 submit`.
    
4. **Update Your Workspace View:**
Modify your Perforce client workspace view to map to your new feature branch.
    
    ```
    p4 client <your_client_name> # or just p4 client to edit current
    
    ```
    
    Edit the `View:` section to point to your feature branch:
    
    ```
    //depot/project/features/my-new-feature/... //your_client_name/...
    
    ```
    
    Save and exit.
    
5. **Sync to Your New Feature Branch:**
    
    ```
    p4 sync //depot/project/features/my-new-feature/...
    
    ```
    
    Now your workspace contains the files from your new feature branch, and you can start working.
    

## 5. Workflow - Working on a Feature Branch

Work on your feature branch as you normally would, making changes and submitting them.

1. **Edit Files:**
    
    ```
    p4 edit <file_name>
    
    ```
    
2. **Add New Files:**
    
    ```
    p4 add <new_file_name>
    
    ```
    
3. **Delete Files:**
    
    ```
    p4 delete <file_name>
    
    ```
    
4. **Submit Changes:**
    
    ```
    p4 submit -d "Description of your changes for this commit."
    
    ```
    
    - Regularly submit your changes to your feature branch to save your progress and create checkpoints.
5. **Keep Your Feature Branch Updated (from `develop`):**
Periodically, you'll want to pull in the latest changes from `develop` into your feature branch to avoid large integration conflicts later.
    
    ```
    # Ensure your workspace is mapped to your feature branch
    p4 client # Verify View: //depot/project/features/my-new-feature/... //your_client_name/...
    
    p4 integrate //depot/project/develop/... //depot/project/features/my-new-feature/...
    p4 resolve -am # Auto-resolve merges, manually resolve others
    p4 submit -d "Integrated latest changes from develop into feature branch."
    
    ```
    

## 6. Workflow - Creating a Review (Pull Request Equivalent)

Once your feature is complete and tested on your branch, you'll prepare it for review. In Perforce, this is typically done by shelving your changes.

1. **Ensure All Changes are in a Single Changelist (or a few related ones):**
If you have multiple pending changelists, you might want to combine them or shelve them individually. For simplicity, let's assume your feature's changes are in your default changelist or a single numbered changelist.
2. **Shelve Your Changes:**
    
    ```
    p4 shelve -c default # Shelves changes in your default changelist
    # OR for a numbered changelist:
    p4 shelve -c <changelist_number>
    
    ```
    
    - This uploads your pending changes to the depot without submitting them. They are now visible to others.
3. **Notify Reviewers:**
    - Inform your team members (e.g., via chat, email, or a dedicated review tool if integrated with Perforce) that your shelved changelist is ready for review.
    - Provide the changelist number and a brief description of the feature.
    - **Reviewers:** Can unshelve your changes into their own workspace to test and review:
        
        ```
        p4 unshelve -s <shelved_changelist_number> -c default # Unshelves into their default changelist
        
        ```
        
        They can then inspect the files, compile, run tests, and add comments.
        
4. **Address Feedback:**
    - Based on review feedback, make necessary changes in your workspace.
    - After making changes, update your shelved changelist:
        
        ```
        p4 shelve -r -c default # Reshelves the updated changes
        # OR for a numbered changelist:
        p4 shelve -r -c <changelist_number>
        
        ```
        
    - Repeat until the review is approved.

## 7. Workflow - Merging a Feature Branch

Once your feature has been reviewed and approved, you will integrate it back into the `develop` branch.

**Prerequisites:**

- Your feature branch is up-to-date with `develop` (you've integrated `develop` into your feature branch recently).
- All your changes on the feature branch are submitted (no pending changes).
- The review process is complete and approved.

**Steps:**

1. **Switch Your Workspace to `develop`:**
Modify your Perforce client workspace view to map back to the `develop` branch.
    
    ```
    p4 client <your_client_name> # or just p4 client to edit current
    
    ```
    
    Edit the `View:` section to point to `develop`:
    
    ```
    //depot/project/develop/... //your_client_name/...
    
    ```
    
    Save and exit.
    
2. **Sync to `develop`:**
    
    ```
    p4 sync //depot/project/develop/...
    
    ```
    
3. **Integrate Your Feature Branch into `develop`:**
    
    ```
    p4 integrate //depot/project/features/my-new-feature/... //depot/project/develop/...
    
    ```
    
    - This creates a pending changelist with the changes from your feature branch.
4. **Resolve Conflicts (if any):**
    
    ```
    p4 resolve -am # Auto-resolve merges, manually resolve others
    
    ```
    
    - Perforce will guide you through any conflicts. Use `p4 resolve` to pick versions or manually edit files.
5. **Submit the Integrated Changes:**
    
    ```
    p4 submit -d "Merge feature: my-new-feature into develop. [Review CL: <shelved_changelist_number>]"
    
    ```
    
    - Include a clear commit message, referencing the feature and the review changelist if applicable.
6. **Delete the Feature Branch (Optional but Recommended):**
Once the feature is successfully merged into `develop` and confirmed, you can delete the feature branch from the depot.
    
    ```
    p4 obliterate //depot/project/features/my-new-feature/...
    # OR, if you want to keep history but mark it for deletion:
    p4 delete //depot/project/features/my-new-feature/...
    p4 submit -d "Deleted feature branch: my-new-feature after merge."
    
    ```
    
    - `p4 obliterate` permanently removes the history. Use with caution.
    - `p4 delete` marks the files for deletion in a changelist, preserving history.

## 8. Best Practices

- **Small, Atomic Commits (Submits):** Break down your work into logical, small changes. Each submit should represent a complete, functional unit of work.
- **Descriptive Changelist Descriptions:** Write clear and concise descriptions for your submits. Explain *what* was changed and *why*.
- **Regular Syncing:** Sync your workspace frequently to get the latest changes from the depot.
- **Frequent Integrations (from `develop` to feature):** Integrate `develop` into your feature branch regularly to minimize merge conflicts later.
- **Test Before Submitting/Reviewing:** Always ensure your code compiles and passes tests before submitting or shelving for review.
- **Communicate:** Keep your team informed about your branching activities and review status.

## 9. Commands Reference

| Command | Description |
| --- | --- |
| `p4 client` | Edit your client workspace specification. |
| `p4 sync <path>` | Sync your workspace to the latest revision of files at the specified path. |
| `p4 edit <file>` | Open a file for editing. |
| `p4 add <file>` | Open a file for adding to the depot. |
| `p4 delete <file>` | Open a file for deleting from the depot. |
| `p4 submit -d "..."` | Submit pending changes to the depot. |
| `p4 populate <src> <dst>` | Copy files from source to destination, creating new history. Used for branching. |
| `p4 integrate <src> <dst>` | Integrate changes from source to destination. Used for merging. |
| `p4 resolve` | Resolve conflicts after an integration. |
| `p4 shelve -c <cl>` | Shelve pending changes in a changelist for review. |
| `p4 unshelve -s <cl>` | Unshelve changes from a shelved changelist. |
| `p4 obliterate <path>` | Permanently remove files and their history from the depot. Use with extreme caution. |

This guide provides a foundation for implementing a more Git-like branching workflow in Perforce. Adapt it to your team's specific needs and project structure.
