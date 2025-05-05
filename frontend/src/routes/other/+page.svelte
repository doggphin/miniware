<script lang="ts">
    import { onMount } from 'svelte';
    import { makeBackendCall, sanitizePartOfURI } from '$lib/scripts/backend';
    import { StatusMessage } from '$lib/scripts/statusMessage';
    import InputField from '$lib/components/InputField.svelte';
    import Button from '$lib/components/Button.svelte';
    import Section from '$lib/components/Section.svelte';
    import StatusMessageDisplay from '$lib/components/StatusMessageDisplay.svelte';

    // Define interfaces for the response data structure
    interface ImageData {
        normal_count: number;
        handscans_count: number;
        oversized_handscans_count: number;
        dpi: number | string;
    }

    interface AudioData {
        files: number;
        length: number;
        fileTypes: string;
    }

    interface VideoData {
        files: number;
        length: number;
    }

    interface FolderData {
        images?: ImageData;
        audio?: AudioData;
        video?: VideoData;
    }

    interface ProblematicFiles {
        "incorrect name": string[];
        "unrecognized file type": string[];
    }

    interface ResultData {
        [folderName: string]: FolderData | ProblematicFiles;
        problematic_files: ProblematicFiles;
    }

    let folderPath = $state('');
    let statusMessage = $state(new StatusMessage("", ""));
    let results: ResultData | null = $state(null);

    async function handleManualFinalCheck() {
        if (!folderPath) {
            statusMessage = StatusMessage.errorMessage('Please enter a folder path');
            return;
        }

        statusMessage = StatusMessage.normalMessage('Analyzing folder...');
        
        try {
            const sanitizedPath = sanitizePartOfURI(folderPath);
            const endpoint = `other/manualFinalCheck/${sanitizedPath}/`;
            
            const response = await fetch(`http://${window.location.hostname}:8000/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to analyze folder');
            }
            
            results = await response.json();
            statusMessage = StatusMessage.successMessage('Folder analysis complete');
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'An error occurred';
            statusMessage = StatusMessage.errorMessage(errorMessage);
        }
    }

    function getFileTypeColor(fileType: string): string {
        if (fileType === 'mp3') return 'green';
        if (fileType === 'wav') return 'orange';
        return 'inherit';
    }

    function formatSeconds(seconds: number): string {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        
        return [
            hours.toString().padStart(2, '0'),
            minutes.toString().padStart(2, '0'),
            remainingSeconds.toString().padStart(2, '0')
        ].join(':');
    }

    function isDpiMultiple(dpiValue: string | number): boolean {
        return typeof dpiValue === 'string' && dpiValue.includes(',');
    }

    async function handleDeleteProblematicFiles() {
        // Combine both types of problematic files
        const filesToDelete = [
            ...(results?.problematic_files['unrecognized file type'] || []),
            ...(results?.problematic_files['incorrect name'] || [])
        ];
        
        if (!folderPath || !results || filesToDelete.length === 0) {
            statusMessage = StatusMessage.errorMessage('No problematic files to delete');
            return;
        }

        if (!confirm('Are you sure you want to delete all problematic files (both unrecognized types and incorrect names)? This action cannot be undone.')) {
            return;
        }

        statusMessage = StatusMessage.normalMessage('Deleting problematic files...');
        
        try {
            const sanitizedPath = sanitizePartOfURI(folderPath);
            const endpoint = `other/deleteFiles/${sanitizedPath}/`;
            
            const response = await fetch(`http://${window.location.hostname}:8000/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_paths: filesToDelete
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to delete files');
            }
            
            const deleteResult = await response.json();
            statusMessage = StatusMessage.successMessage(`Successfully deleted ${deleteResult.total_deleted} files`);
            
            // Clear the problematic files arrays to hide the problematic files section
            if (results) {
                results.problematic_files['incorrect name'] = [];
                results.problematic_files['unrecognized file type'] = [];
            }
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'An error occurred';
            statusMessage = StatusMessage.errorMessage(errorMessage);
        }
    }
</script>

<svelte:head>
    <title>Manual Final Check</title>
</svelte:head>


<Section title="Folder Analysis">
    {#snippet helpContent()}
        <div class="help-content">
            <p> - This feature analyzes a folder for various media types and checks for problematic files. </p>
            <p> - It provides detailed information about the contents of the folder, including images, audio, and video files. </p>
            <p> - You can also delete problematic files directly from this interface. </p>
        </div>
    {/snippet}
    <InputField 
        title="Folder Path" 
        bind:inputState={folderPath} 
        placeholderText="Folder path"
    />
    <div class="spacer"></div>
    <Button onClick={handleManualFinalCheck}>
        Analyze!
    </Button>
    <div class="spacer"></div>
    <StatusMessageDisplay statusMessage={statusMessage} />
    
    {#if results}
        <div class="results">
            <h2>Analysis Results</h2>
            
            {#each Object.entries(results)
                .filter(([key]) => key !== 'problematic_files')
                .sort(([keyA], [keyB]) => {
                    // Ensure "Main Folder" always appears first
                    if (keyA === "Main Folder") return -1;
                    if (keyB === "Main Folder") return 1;
                    return keyA.localeCompare(keyB);
                }) as [folderName, data] }
                {@const folderData = data as FolderData}
                <div class="folder-section">
                    <h3>{folderName}</h3>
                    
                    {#if 'images' in folderData && folderData.images}
                        <div class="media-section">
                            <h4>Images</h4>
                            <ul>
                                <li>Normal Images: {folderData.images.normal_count}</li>
                                <li>Handscans: {folderData.images.handscans_count}</li>
                                <li>Oversized Handscans: {folderData.images.oversized_handscans_count}</li>
                                <li>DPI: <span class={isDpiMultiple(folderData.images.dpi) ? 'error' : ''}>{folderData.images.dpi}</span></li>
                            </ul>
                        </div>
                    {/if}
                    
                    {#if 'audio' in folderData && folderData.audio}
                        <div class="media-section">
                            <h4>Audio</h4>
                            <ul>
                                <li>Files: {folderData.audio.files}</li>
                                <li>Total Length: {formatSeconds(folderData.audio.length)}</li>
                                <li>File Types: 
                                    {#each folderData.audio.fileTypes.split(', ') as fileType}
                                        <span style="color: {getFileTypeColor(fileType)};">{fileType}</span>
                                        {#if fileType !== folderData.audio.fileTypes.split(', ').slice(-1)[0]}, {/if}
                                    {/each}
                                </li>
                            </ul>
                        </div>
                    {/if}
                    
                    {#if 'video' in folderData && folderData.video}
                        <div class="media-section">
                            <h4>Video</h4>
                            <ul>
                                <li>Files: {folderData.video.files}</li>
                                <li>Total Length: {formatSeconds(folderData.video.length)}</li>
                            </ul>
                        </div>
                    {/if}
                </div>
            {/each}
            
            {#if results.problematic_files}
                <div class="problematic-files">
                    <h3>Problematic Files</h3>
                    
                    {#if results.problematic_files['incorrect name']?.length > 0}
                        <div class="problem-section">
                            <h4>Incorrect Name</h4>
                            <ul>
                                {#each results.problematic_files['incorrect name'] as file}
                                    <li>{file}</li>
                                {/each}
                            </ul>
                        </div>
                    {/if}
                    
                    {#if results.problematic_files['unrecognized file type']?.length > 0}
                        <div class="problem-section">
                            <h4>Unrecognized File Type</h4>
                            <ul>
                                {#each results.problematic_files['unrecognized file type'] as file}
                                    <li>{file}</li>
                                {/each}
                            </ul>
                        </div>
                    {/if}
                    
                    {#if (results.problematic_files['incorrect name']?.length > 0 || results.problematic_files['unrecognized file type']?.length > 0)}
                        <div class="action-buttons">
                            <Button 
                                onClick={handleDeleteProblematicFiles} 
                                text={`Delete All Problematic Files (${(results.problematic_files['incorrect name']?.length || 0) + (results.problematic_files['unrecognized file type']?.length || 0)})`} 
                            />
                        </div>
                    {/if}
                </div>
            {/if}
        </div>
    {/if}
</Section>

<style>
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    h1 {
        margin-bottom: 20px;
    }
    
    h2 {
        font-size: var(--s32);
        margin-bottom: var(--s16);
        font-weight: bold;
    }
    
    h3 {
        font-size: var(--s24);
        margin-bottom: var(--s8);
        font-weight: bold;
    }
    
    h4 {
        font-size: var(--s20);
        margin-bottom: var(--s8);
        font-weight: bold;
    }
    
    .spacer {
        width: 100%;
        height: 20px;
    }
    
    .results {
        margin-top: 30px;
    }
    
    .folder-section {
        margin-bottom: 30px;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    
    .media-section {
        margin-top: 15px;
        padding: 10px;
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    
    .problematic-files {
        margin-top: 30px;
        padding: 15px;
        border: 1px solid #f8d7da;
        background-color: #fff5f5;
        border-radius: 5px;
    }
    
    .problem-section {
        margin-top: 15px;
    }
    
    .error {
        color: red;
        font-weight: bold;
    }
    
    ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    li {
        margin-bottom: 5px;
    }
    
    .action-buttons {
        margin-top: 15px;
        display: flex;
        justify-content: flex-end;
    }
</style>
