<script lang="ts">
    import Section from "$lib/components/Section.svelte";
    import InputField from "$lib/components/InputField.svelte";
    import OptionsField from "$lib/components/OptionsField.svelte";
    import { StatusMessage } from "$lib/scripts/statusMessage";
    import { makeBackendCall, sanitizePartOfURI } from "$lib/scripts/backend";
    import StatusMessageDisplay from "$lib/components/StatusMessageDisplay.svelte";
    import Button from "$lib/components/Button.svelte";
    import CheckField from "$lib/components/CheckField.svelte";

    let statusMessage = $state(new StatusMessage("", ""));
    function setStatusMessage(newStatusMessage : StatusMessage) {
        statusMessage = newStatusMessage;
    }

    const corrState = $state({
        mediaType : "",
        fromFolder : "",
        toFolder : "",
        baseFolder : "",
    });

    let slidesDisableCrop = $state(false);
    let slidesDisableColorCorrection = $state(false);
    let slidesEnforcedAspectRatio = $state("");
    const enforcedAspectRatios = [
        "Any",
        "4:3",
        "3:2",
        "1:1"
    ];
    
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

        await makeBackendCall(endpoint, "POST", {
            "options" : {
                "slidesDisableCrop" : slidesDisableCrop,
                "slidesDisableColorCorrection" : slidesDisableColorCorrection,
                "slidesEnforceAspectRatio" : slidesEnforcedAspectRatio
            }
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
        "VHS" : async() => makeCorrectRequest("vhs"),
        "Everything" : async() => makeCorrectRequest("all")
    }


    async function correct() {
        console.log("Correcting!");
        await (mediaTypeToCorrectionDelegate[corrState.mediaType] || noMediaTypeSelected)();
    }
</script>


<Section title="Correct Media">
    <ol>
        <li><OptionsField title="Media Type" bind:optionState={corrState.mediaType} options={Object.keys(mediaTypeToCorrectionDelegate)} unselectedText="Media Type"/></li>
        {#if corrState.mediaType == "Slides" || corrState.mediaType == "Everything"}
            <li><CheckField title="Disable Slides Cropping" bind:enabledState={slidesDisableCrop}/></li>
            <li><CheckField title="Disable Slides Color Correction" bind:enabledState={slidesDisableColorCorrection}/></li>
            <li><OptionsField title="Enforce Slides Aspect Ratio" bind:optionState={slidesEnforcedAspectRatio} options={enforcedAspectRatios} unselectedText={enforcedAspectRatios[0]}/></li>
        {/if}
        {#if corrState.mediaType != "Everything"}
            <li><InputField title="From Folder" bind:inputState={corrState.fromFolder}/></li>
            <li><InputField title="To Folder" bind:inputState={corrState.toFolder}/></li>
        {:else}
            <li><InputField title="Project Folder" bind:inputState={corrState.baseFolder}/></li>
        {/if}
    </ol>
    <Button text="Correct!" onClick={correct} />
    <StatusMessageDisplay statusMessage={statusMessage}/>
</Section>



<style>
    li {
        display: block;
        margin-bottom: var(--s16);
    }
</style>