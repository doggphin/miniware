<script lang="ts">
    import InputField from "$lib/components/InputField.svelte";
    import CheckField from "$lib/components/CheckField.svelte";
    import OptionsField from "$lib/components/OptionsField.svelte";
    import Section from "$lib/components/Section.svelte";
    import { parseGoogleSheetsUrlOrError } from "$lib/scripts/verifiers";
    import { getBackendAddress, sanitizePartOfURI, makeBackendCall } from "$lib/scripts/backend";
    import { StatusMessage } from "$lib/scripts/statusMessage";

    let statusMessage = $state(new StatusMessage("", ""));
    function setStatusMessage(message : StatusMessage) {
        statusMessage = message;
    }

    const sheetsOptions = $state({
        useGoogleSheets : true,
        url : "",
        checkAllAtOnce : false,
    });
    const mediaTypeOptions = ["Photo",];
    const sharedOptions = $state({
        group: "",
        mediaType : "",
    })
    const manualOptions = $state({
        firstName : "",
        lastName : "",
        projectFolderName : "",
        hasCorrectedItems : false,
        customGroupFolderName : "",
    })
    const dpiOptions = ["300", "600", "1200", "1250", "2500", "3000", "5000"];
    const photoTypeOptions = ["Slides", "Prints", "Negs"];
    const manualPhotoOptions = $state({
        photoType : "",
        dpi : "",
        normalScansCount : "",
        handScansCount : "",
        oshScansCount : "",
    })


    function tryParseUrl() : boolean {
        return parseGoogleSheetsUrlOrError(
            sheetsOptions.url, 
            (newUrl : string) => { sheetsOptions.url = newUrl; }, 
            setStatusMessage
        );
    }


    async function autoFinalCheck() {
        if(!tryParseUrl()) {
            return;
        }

        if(!sharedOptions.group) {
            statusMessage = StatusMessage.errorMessage("Please set a group ID!");
        }

        const endpoints: Record<string, string> = {
            "Photo": `fc/check_photo_row/${sheetsOptions.url}/${sharedOptions.group}`,
        };

        const endpoint = endpoints[sharedOptions.mediaType];

        await makeBackendCall(endpoint, setStatusMessage);
    }


    async function autoFinalCheckAll() {
        if(!tryParseUrl()) {
            return;
        }

        const endpoints: Record<string, string> = {
            "Photo": `fc/check_all_photo_rows/${sheetsOptions.url}`,
        };
        
        const endpoint = endpoints[sharedOptions.mediaType];

        await makeBackendCall(endpoint, setStatusMessage);
    }


    /** Sends a final check request to the backend. */
    async function manualFinalCheck() {
        function getProjectEndpointData() : string {
            return `${manualOptions.firstName}/` +
                `${manualOptions.lastName}/` +
                `${manualOptions.projectFolderName}/`
        }

        /** Checks each {variable name : variable} pair passed in. If all exist, return true. If not, returns false, and sets an error. */
        function ensureFieldsExist(requiredNameVariablePairs : {[key:string] : any}) : boolean {
            for(let [key, value] of Object.entries(requiredNameVariablePairs)) {
                if(!value) {
                    StatusMessage.errorMessage(`Please fill out the ${key} field!`);
                    return false;
                }
            }

            return true;
        }
        
        StatusMessage.normalMessage("Thinking...");

        // Make sure all required fields are filled out
        if(!ensureFieldsExist({
            "First Name" : manualOptions.firstName,
            "Last Name" : manualOptions.lastName,
            "Project Folder Name" : manualOptions.projectFolderName,
        })) {
            return;
        }

        // Generate the base endpoint for higher-level requests to build off of
        let endpoint = `http://${getBackendAddress()}/fc/`;
        let params : any = {};
        if(sharedOptions.group != "") {
            params["group_number"] = sharedOptions.group;
        }
        if(manualOptions.customGroupFolderName != "") {
            params["custom_group_name"] = manualOptions.customGroupFolderName;
        }
        if(manualOptions.hasCorrectedItems) {
            params["has_corrected_items"] = ""
        }

        // Mutate endpoint to be set up for whatever media type is requested
        switch(sharedOptions.mediaType) {
            case "Photo":
                if(!ensureFieldsExist({
                    "Photo type" : manualPhotoOptions.photoType,
                    "DPI" : manualPhotoOptions.dpi
                })) {
                    return;
                }
                endpoint += "fc/photo/";
                endpoint += getProjectEndpointData();
                endpoint += 
                    `${manualPhotoOptions.dpi}/` +
                    `${manualPhotoOptions.photoType}/`;
                if(manualPhotoOptions.normalScansCount != "") {
                    params["count_reg"] = manualPhotoOptions.normalScansCount;
                }
                if(manualPhotoOptions.handScansCount != "") {
                    params["count_hs"] = manualPhotoOptions.handScansCount;
                }
                if(manualPhotoOptions.oshScansCount != "") {
                    params["count_oshs"] = manualPhotoOptions.oshScansCount;
                }

                break;
            default:
                statusMessage = StatusMessage.errorMessage("Must set media type field!");
                return;
        }

        // Make a call to the finished endpoint
        console.log(endpoint);
        endpoint = encodeURI(endpoint);
        endpoint = sanitizePartOfURI(endpoint);
        let endpointUrl = new URL(endpoint);
        endpointUrl.search = new URLSearchParams(params).toString();
        const response = await fetch(endpointUrl);
        const responseJson = await response.json();

        if(response.status == 200) {
            statusMessage = StatusMessage.successMessage(responseJson["message"]);
        } else {
            statusMessage = StatusMessage.errorMessage(responseJson["message"] ?? "Unknown error!");
        }
    }
</script>


<Section title="Final Check">
    <!-- Determines what the final check button does -->
    {@const finalCheckDelegate = !sheetsOptions.useGoogleSheets ?  
        manualFinalCheck : sheetsOptions.checkAllAtOnce ?
        autoFinalCheckAll :
        autoFinalCheck
    }
    <ol>
        <li>Use google sheets: <CheckField bind:enabledState={sheetsOptions.useGoogleSheets}/></li>
        <li>Media Type: <OptionsField bind:optionState={sharedOptions.mediaType} options={mediaTypeOptions} unselectedText="Media Type"/></li>
        {#if sheetsOptions.useGoogleSheets}
            <li>Check all groups: <CheckField bind:enabledState={sheetsOptions.checkAllAtOnce}/></li>
            <li>Project URL: <InputField bind:inputState={sheetsOptions.url}/></li>
        {/if}
        {#if !sheetsOptions.useGoogleSheets || !sheetsOptions.checkAllAtOnce}
            <li>Group Number / Identifier: <InputField bind:inputState={sharedOptions.group}/></li>
        {/if}
        {#if !sheetsOptions.useGoogleSheets} 
            <div class="vertical-spacer"></div>
            <li>First Name: <InputField bind:inputState={manualOptions.firstName}/></li>
            <li>Last Name: <InputField bind:inputState={manualOptions.lastName}/></li>
            <li>Project Folder Name: <InputField bind:inputState={manualOptions.projectFolderName}/></li>
            <li>Project has Corrected + Raw folders: <CheckField bind:enabledState={manualOptions.hasCorrectedItems}/></li>
            <li>Custom Group Folder Name: <InputField bind:inputState={manualOptions.customGroupFolderName}/></li>

            {#if sharedOptions.mediaType == "Photo"}
                <div class="vertical-spacer"></div>
                <li>Photo type: <OptionsField bind:optionState={manualPhotoOptions.photoType} options={photoTypeOptions} unselectedText="Photo Type"/></li>
                <li>DPI options: <OptionsField bind:optionState={manualPhotoOptions.dpi} options={dpiOptions} unselectedText="DPI"/></li>
                <li>Normal scans count: <InputField bind:inputState={manualPhotoOptions.normalScansCount}/></li>
                <li>Handscans count: <InputField bind:inputState={manualPhotoOptions.handScansCount}/></li>
                <li>Oversized Handscans count: <InputField bind:inputState={manualPhotoOptions.oshScansCount}/></li>
            {/if}
        {/if}

        <div class="vertical-spacer"></div>
        <button onclick={finalCheckDelegate}> Final check! </button>

        {#if statusMessage.message}
            <div class="vertical-spacer"></div>
            <li style="color: {statusMessage.status == "error" ? "red" : statusMessage.status == "success" ? "green" : "var(--clr-primary)"};">{statusMessage.message}</li>
        {/if}
    </ol>
</Section>



<style>
    li {
        display: block;
        margin-top: var(--s4);
    }
    .vertical-spacer {
        margin-top: var(--s16);
    }
</style>