<script lang="ts">
    import Section from "$lib/components/Section.svelte";
    import InputField from "$lib/components/InputField.svelte";
    import OptionsField from "$lib/components/OptionsField.svelte";
    import { StatusMessage } from "$lib/scripts/statusMessage";
    import { makeBackendCall, sanitizePartOfURI } from "$lib/scripts/backend";
    import StatusMessageDisplay from "$lib/components/StatusMessageDisplay.svelte";
    import Button from "$lib/components/Button.svelte";
    import CheckField from "$lib/components/CheckField.svelte";
    import Modal from "$lib/components/Modal.svelte";

    import ExampleCorrectionPath from "$lib/assets/example-correction-path.png";
    import ExampleCorrectionPathPasted from "$lib/assets/example-correction-path-pasted.png";


    let statusMessage = $state(new StatusMessage("", ""));
    const corrState = $state({
        mediaType : "",
        fromFolder : "",
        toFolder : "",
        baseFolder : "",
    });
    // Slides options
    let slidesDisableCrop = $state(false);
    let slidesDisableColorCorrection = $state(false);
    let slidesEnforcedAspectRatio = $state("3:2");
    const enforcedAspectRatios = [
        "Any",
        "4:3",
        "3:2",
        "1:1"
    ];
    // Prints options
    let printsDisableCrop = $state(false);
    let printsDisableColorCorrection = $state(false);
    // Audio options
    let audioSilenceThreshholdDb = $state("20");
    const AUDIO_DEFAULT_THRESHOLD = "20"; 
    // VHS options
    let vhsSilenceThreshholdDb = $state("16");
    const VHS_DEFAULT_THRESHOLD = "16";

    let showAdvancedOptions = $state(false);

    
    async function makeCorrectRequest(mediaType : string) {
        let endpoint : string;
        
        statusMessage = StatusMessage.normalMessage("Correcting...")
        if(mediaType == "all") {
            if(corrState.baseFolder == "") {
                statusMessage = StatusMessage.fieldNotSetErrorMessage("Base Folder");
                return
            }

            const sanitizedBaseFolder = sanitizePartOfURI(corrState.baseFolder);
            endpoint = `corr/all/${sanitizedBaseFolder}/`;
        } else {
            if(corrState.fromFolder == "") {
            statusMessage = StatusMessage.fieldNotSetErrorMessage("From Folder");
            return;
            }
            if(corrState.toFolder == "") {
                statusMessage = StatusMessage.fieldNotSetErrorMessage("To Folder");
                return;
            }
            const sanitizedFromFolder = sanitizePartOfURI(corrState.fromFolder);
            const sanitizedToFolder = sanitizePartOfURI(corrState.toFolder);

            endpoint = `corr/${mediaType}/${sanitizedFromFolder}/${sanitizedToFolder}/`;
        }

        // Prepare options object
        const options = {
            // Slides options
            "slidesDisableCrop": slidesDisableCrop,
            "slidesDisableColorCorrection": slidesDisableColorCorrection,
            "slidesEnforceAspectRatio": slidesEnforcedAspectRatio,
            
            // Prints options
            "printsDisableCrop": printsDisableCrop,
            "printsDisableColorCorrection": printsDisableColorCorrection,
            
            // Audio options
            "audioSilenceThreshholdDb": audioSilenceThreshholdDb ? parseInt(audioSilenceThreshholdDb) : parseInt(AUDIO_DEFAULT_THRESHOLD),
            
            // VHS options
            "vhsSilenceThreshholdDb": vhsSilenceThreshholdDb ? parseInt(vhsSilenceThreshholdDb) : parseInt(VHS_DEFAULT_THRESHOLD)
        };

        await makeBackendCall(endpoint, "POST", {
            "options": options
        })
            .then(() => {
                statusMessage = StatusMessage.successMessage("All done!")
            })
            .catch((e) => {
                statusMessage = StatusMessage.errorMessage(e);
            });
    }


    async function noMediaTypeSelected() {
        statusMessage = StatusMessage.errorMessage("Invalid media type selected!");
    }


    const mediaTypeToCorrectionDelegate : Record<string, () => Promise<void>> = {
        "Slides" : async() => makeCorrectRequest("slides"),
        "Prints" : async() => makeCorrectRequest("prints"),
        "Audio" : async() => makeCorrectRequest("audio"),
        "Video" : async() => makeCorrectRequest("vhs"),
        "Everything" : async() => makeCorrectRequest("all")
    }


    async function correct() {
        console.log("Correcting!");
        await (mediaTypeToCorrectionDelegate[corrState.mediaType] || noMediaTypeSelected)();
    }
</script>


<Section title="Correct Media">
    {#snippet helpContent()}
        <ol class="help-content">
            <li>- This feature automatically corrects different types of media for you.</li>
            <li>- It takes files from one folder, corrects them, and saves them to another folder.</li>
            <li>- To select a folder, click on the path of the folder in the File Explorer, copy it (CTRL + C) and paste it in MiniWare (CTRL + V)</li>
            <li>
                <img class="help-image" src={ExampleCorrectionPath} alt="How to copy absolute file paths"/>
            </li>
            <li>
                <img class="help-image" src={ExampleCorrectionPathPasted} alt="How to copy absolute file paths"/>
            </li>
            <li>- You can choose to either do one specific kind of media, or choose "Everything" mode, which selects media for you based on file type and file names. </li>
            <li>- In "Everything" mode, select a folder with a "Raw" and "Corrected" folder in it. All folders will be created in the "Corrected" folder for you and all files will be corrected. </li>
            <li>- If you'd like, you can set options for how files should be corrected.</li>
            <li>- Please note that any files being corrected MUST be on a shared drive, otherwise they can't be accessed by the correction software.</li>
        </ol>
    {/snippet}
    <ol>
        <li><OptionsField title="Media Type" bind:optionState={corrState.mediaType} options={Object.keys(mediaTypeToCorrectionDelegate)} unselectedText="Media Type"/></li>
        
        <!-- Folder input fields moved to the top -->
        {#if corrState.mediaType != "Everything"}
            <li><InputField title="From Folder" bind:inputState={corrState.fromFolder}/></li>
            <li><InputField title="To Folder" bind:inputState={corrState.toFolder}/></li>
        {:else}
            <li><InputField title="Project Folder" bind:inputState={corrState.baseFolder}/></li>
        {/if}
        
        {#if corrState.mediaType}
            <li>
                <button 
                    type="button" 
                    class="styled-button" 
                    onclick={() => showAdvancedOptions = !showAdvancedOptions} 
                    aria-expanded={showAdvancedOptions} 
                    aria-label={showAdvancedOptions ? 'Hide Advanced Options' : 'Show Advanced Options'}>
                    <span>{showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options</span>
                    <span class="toggle-icon">{showAdvancedOptions ? '▲' : '▼'}</span>
                </button>
            </li>
        {/if}
        
        {#if showAdvancedOptions && corrState.mediaType}
            <!-- Slides options -->
            {#if corrState.mediaType == "Slides" || corrState.mediaType == "Everything"}
                {#if corrState.mediaType == "Everything"}
                    <li class="section-title">Slides Options</li>
                {/if}
                <li><CheckField title="Disable Slides Cropping" bind:enabledState={slidesDisableCrop}/></li>
                <li><CheckField title="Disable Slides Color Correction" bind:enabledState={slidesDisableColorCorrection}/></li>
                <li><OptionsField title="Enforce Slides Aspect Ratio (3:2 is normal)" bind:optionState={slidesEnforcedAspectRatio} options={enforcedAspectRatios} unselectedText={enforcedAspectRatios[0]}/></li>
            {/if}
            
            <!-- Prints options -->
            {#if corrState.mediaType == "Prints" || corrState.mediaType == "Everything"}
                {#if corrState.mediaType == "Everything"}
                    <li class="section-title">Prints Options</li>
                {/if}
                <li><CheckField title="Disable Prints Cropping" bind:enabledState={printsDisableCrop}/></li>
                <li><CheckField title="Disable Prints Color Correction" bind:enabledState={printsDisableColorCorrection}/></li>
            {/if}
            
            <!-- Audio options -->
            {#if corrState.mediaType == "Audio" || corrState.mediaType == "Everything"}
                {#if corrState.mediaType == "Everything"}
                    <li class="section-title">Audio Options</li>
                {/if}
                <li><InputField title="Audio Silence Threshold (dB)" bind:inputState={audioSilenceThreshholdDb} numericalOnly={true} placeholderText={`${AUDIO_DEFAULT_THRESHOLD}`}/></li>
            {/if}
            
            <!-- VHS options -->
            {#if corrState.mediaType == "Video" || corrState.mediaType == "Everything"}
                {#if corrState.mediaType == "Everything"}
                    <li class="section-title">Video Options</li>
                {/if}
                <li><InputField title="Video Silence Threshold (dB)" bind:inputState={vhsSilenceThreshholdDb} numericalOnly={true} placeholderText={`${VHS_DEFAULT_THRESHOLD}`}/></li>
            {/if}
        {/if}
    </ol>
    <Button onClick={correct}>Correct!</Button>
    <StatusMessageDisplay statusMessage={statusMessage}/>
</Section>


<style>
    .help-content {
        text-align: left;
    }

    .help-image {
        max-width: 100%;
        border: 2px solid black;
        border-radius: var(--s8);
    }

    li {
        display: block;
        margin-bottom: var(--s16);
    }
    
    .section-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-top: var(--s24);
        margin-bottom: var(--s8);
    }
    
    .toggle-icon {
        font-size: 12px;
        margin-left: 8px;
    }
</style>
