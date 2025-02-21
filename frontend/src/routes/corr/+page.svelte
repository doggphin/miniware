<script lang="ts">
    import Section from "$lib/components/Section.svelte";
    import InputField from "$lib/components/InputField.svelte";
    import OptionsField from "$lib/components/OptionsField.svelte";
    import { StatusMessage } from "$lib/scripts/statusMessage";
    import { makeBackendCall, sanitizePartOfURI } from "$lib/scripts/backend";
    import StatusMessageDisplay from "$lib/components/StatusMessageDisplay.svelte";

    let statusMessage = $state(new StatusMessage("", ""));
    function setStatusMessage(newStatusMessage : StatusMessage) {
        statusMessage = newStatusMessage;
    }

    const mediaTypeOptions = ["Slides", "Prints"]
    const corrState = $state({
        mediaType : "",
        fromFolder : "",
        toFolder : ""
    });

    async function correctSlides() {
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

        const endpoint = `corr/slides/${sanitizedFromFolder}/${sanitizedToFolder}/`;
        makeBackendCall(endpoint, setStatusMessage, "POST");
    }


    async function correctPrints() {
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

        const endpoint = `corr/prints/${sanitizedFromFolder}/${sanitizedToFolder}/`;
        makeBackendCall(endpoint, setStatusMessage, "POST");
    }


    async function noMediaTypeSelected() {
        console.log("no media type");
        statusMessage = StatusMessage.errorMessage("Invalid media type selected!");
    }


    const mediaTypeToCorrectionDelegate : Record<string, () => void> = {
        "Slides" : correctSlides,
        "Prints" : correctPrints,
    }


    async function correct() {
        console.log("Correcting!");
        const delegate = mediaTypeToCorrectionDelegate[corrState.mediaType] || noMediaTypeSelected;
        delegate();
    }
</script>


<Section title="Correct Media">
    <ol>
        <li>Media Type: <OptionsField bind:optionState={corrState.mediaType} options={mediaTypeOptions} unselectedText="Media Type"/></li>
        <li>From Folder: <InputField bind:inputState={corrState.fromFolder}/></li>
        <li>To Folder: <InputField bind:inputState={corrState.toFolder}/></li>
    </ol>
    <button onclick={correct}>
        Correct!
    </button>
    <StatusMessageDisplay statusMessage={statusMessage}/>
</Section>



<style>
    li {
        display: block;
        margin-top: var(--s4);
    }
</style>