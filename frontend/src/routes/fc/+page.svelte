<script lang="ts">
    import InputField from "$lib/components/InputField.svelte";
    import CheckField from "$lib/components/CheckField.svelte";
    import OptionsField from "$lib/components/OptionsField.svelte";
    import Button from "$lib/components/Button.svelte";
    import { getBackendAddress } from "$lib/scripts/backend";

    let statusMessage = $state("");
    let statusMessageType = $state("");

    const sheetsOptions = $state({
        url : ""
    });


    const mediaTypeOptions = ["Photo",];
    const requiredOptions = $state({
        group: "",
        mediaType : "",
        checkAllAtOnce : false,
    })


    const autoFillableOptions = $state({
        firstName : "",
        lastName : "",
        projectFolderName : "",
        hasCorrectedItems : false,
        customGroupFolderName : "",
    })


    const dpiOptions = ["300", "600", "1200", "1250", "2500", "3000", "5000"];
    const photoTypeOptions = ["Slides", "Prints", "Negs"];
    const photoOptions = $state({
        photoType : "",
        dpi : "",
        normalScansCount : "",
        handScansCount : "",
        oshScansCount : "",
    })


    function setStatusMessage(message : string, messageType: string) {
        statusMessage = message;
        statusMessageType = messageType;
    }
    function setError(error : string) {
        setStatusMessage(error, "error");
    }
    function addError(error : string) {
        setStatusMessage(`${statusMessage ? `${statusMessage}, ` : ""}${error}`, "error");
    }
    function setMessage(message : string) {
        setStatusMessage(message, "");
    }
    function setSuccess(success : string) {
        setStatusMessage(success, "succcess");
    }
    function clearStatus() {
        setStatusMessage("", "");
    }


    function tryParseGoogleSheetsUrl() : boolean {
        if(sheetsOptions.url.includes("/")) {
            const split = sheetsOptions.url.split("/");
            if(split.length != 7) {
                setError("Please enter a valid URL! Either copy the entire google sheets link, or just the sheet ID.");
                return false;
            }
            sheetsOptions.url = split[5];
        }
        
        return true;
    }


    async function finalCheckAll() {
        setMessage("Thinking...");

        if(!tryParseGoogleSheetsUrl()) {
            return;
        }
        
        let backendAddress = `${getBackendAddress()}/fc/`;
        switch(requiredOptions.mediaType) {
            case "Photo":
                backendAddress += "check_all_photo_rows/";
                break;
        }
        backendAddress += `${sheetsOptions.url}/`;

        const response = await fetch(backendAddress);
        const responseJson = await response.json();

        if(response.status == 200) {
            setSuccess(responseJson["message"]);
        } else {
            setError(responseJson["message"] ?? "Unknown error!");
        }
    }


    async function fillFieldsFromURL() {
        if(sheetsOptions.url == "") {
            setError("Please set the google sheets URL!");
            return;
        }
        if(requiredOptions.mediaType == "") {
            setError("Please set media type!");
            return;
        }
        if(requiredOptions.group == "") {
            setError("Please set the group number to check!");
            return;
        }

        clearStatus();
        statusMessage = "Thinking...";

        const backendAddress = getBackendAddress();
        const baseEndpoint = `${backendAddress}/fc/`;
        if(!tryParseGoogleSheetsUrl()) {
            return;
        }
        const url = sheetsOptions.url;
        
        const clientInfoEndpoint = baseEndpoint + `client_info/${url}/`;
        const clientInfoResponse = await fetch(clientInfoEndpoint);
        if(clientInfoResponse.status == 200) {
            const clientInfoJson = await clientInfoResponse.json();
            const clientInfoMessage = clientInfoJson["message"];
            autoFillableOptions.firstName = clientInfoMessage["client_first_name"];
            autoFillableOptions.lastName = clientInfoMessage["client_last_name"];
            // Replace the project folder name with the media type being checked
            const projectFolderName = clientInfoMessage["title"];
            const [name, _, date] = projectFolderName.split("_");
            autoFillableOptions.projectFolderName = `${name}_${requiredOptions.mediaType}_${date}`
        } else {
            addError("Couldn't get client name from sheets!");
        }
        
        const correctedEndpoint = baseEndpoint + `photo_has_corrected/${url}/`;
        const correctedEndpointResponse = await fetch(correctedEndpoint);
        if(correctedEndpointResponse.status == 200) {
            const correctedJson = await correctedEndpointResponse.json();
            const correctedMessage = correctedJson["message"];
            console.log(correctedMessage["message"]);
            autoFillableOptions.hasCorrectedItems = correctedMessage["has_corrected_items"];
        } else {
            addError("Couldn't get if the project had corrected files from sheets!");
        }
        
        let rowMessage : any = {};
        switch(requiredOptions.mediaType) {
            case "Photo":
                const photoRowEndpoint = baseEndpoint + `photo_info_normal_row/${url}/${parseInt(requiredOptions.group)}`;
                const photoRowResponse = await fetch(photoRowEndpoint);
                if(photoRowResponse.status == 200) {
                    const photoRowJson = await photoRowResponse.json();
                    rowMessage = photoRowJson["message"];
                    
                    photoOptions.dpi = rowMessage["dpi"];
                    console.log(photoOptions.dpi);
                    photoOptions.normalScansCount = rowMessage["lp"];
                    photoOptions.handScansCount = rowMessage["hs"];
                    photoOptions.oshScansCount = rowMessage["oshs"];
                    photoOptions.photoType = rowMessage["photo_type"];
                    // Google sheets calls "prints" "print". Rename it here, asking Gwen to fix on google sheets
                    if(photoOptions.photoType == "Print") {
                        photoOptions.photoType = "Prints";
                    }
                } else {
                    addError("Couldn't get photo row information from sheets!");
                    return;
                }
                break;
        }
        autoFillableOptions.customGroupFolderName = rowMessage["custom_folder_name"];
    }


    /** Sends a final check request to the backend. */
    async function finalCheck() {
        if(requiredOptions.checkAllAtOnce) {
            await finalCheckAll();
            return;
        }

        function getProjectEndpointData() : string {
            return `${autoFillableOptions.firstName}/` +
                `${autoFillableOptions.lastName}/` +
                `${autoFillableOptions.projectFolderName}/`
        }

        /** Checks each {variable name : variable} pair passed in. If all exist, return true. If not, returns false, and sets an error. */
        function ensureFieldsExist(requiredNameVariablePairs : {[key:string] : any}) : boolean {
            for(let [key, value] of Object.entries(requiredNameVariablePairs)) {
                if(!value) {
                    setError(`Please fill out the ${key} field!`);
                    return false;
                }
            }

            return true;
        }
        
        setMessage("Thinking...");

        // Make sure all required fields are filled out
        if(!ensureFieldsExist({
            "First Name" : autoFillableOptions.firstName,
            "Last Name" : autoFillableOptions.lastName,
            "Project Folder Name" : autoFillableOptions.projectFolderName,
        })) {
            return;
        }

        // Generate the base endpoint for higher-level requests to build off of
        let endpoint = `http://${getBackendAddress()}/`;
        let params : any = {};
        if(requiredOptions.group != "") {
            params["group_number"] = requiredOptions.group;
        }
        if(autoFillableOptions.customGroupFolderName != "") {
            params["custom_group_name"] = autoFillableOptions.customGroupFolderName;
        }
        if(autoFillableOptions.hasCorrectedItems) {
            params["has_corrected_items"] = ""
        }

        // Mutate endpoint to be set up for whatever media type is requested
        switch(requiredOptions.mediaType) {
            case "Photo":
                if(!ensureFieldsExist({
                    "Photo type" : photoOptions.photoType,
                    "DPI" : photoOptions.dpi
                })) {
                    return;
                }
                endpoint += "fc/photo/";
                endpoint += getProjectEndpointData();
                endpoint += 
                    `${photoOptions.dpi}/` +
                    `${photoOptions.photoType}/`;
                if(photoOptions.normalScansCount != "") {
                    params["count_reg"] = photoOptions.normalScansCount;
                }
                if(photoOptions.handScansCount != "") {
                    params["count_hs"] = photoOptions.handScansCount;
                }
                if(photoOptions.oshScansCount != "") {
                    params["count_oshs"] = photoOptions.oshScansCount;
                }

                break;
            default:
                setError("Must set media type field!");
                return;
        }

        // Make a call to the finished endpoint
        console.log(endpoint);
        endpoint = encodeURI(endpoint);
        endpoint = endpoint.replace(/#/g, "%23");  // Replace hashtags with %23
        let endpointUrl = new URL(endpoint);
        endpointUrl.search = new URLSearchParams(params).toString();
        const response = await fetch(endpointUrl);
        const responseJson = await response.json();

        if(response.status == 200) {
            setSuccess(responseJson["message"]);
        } else {
            setError(responseJson["message"] ?? "Unknown error!");
        }
    }
</script>



<div class="vertical-spacer"></div>
<ol>
    <li>
        <div>
            <span>Check all groups of media type (requires google sheets)?</span>
            <CheckField bind:enabledState={requiredOptions.checkAllAtOnce}/>
        </div>
    </li>
    <li>
        Media Type: <OptionsField bind:optionState={requiredOptions.mediaType} options={mediaTypeOptions} unselectedText="Media Type"/>
    </li>
    <li>
        Autofill from Project URL: <InputField bind:inputState={sheetsOptions.url}/>
        <Button onClick={fillFieldsFromURL} text="Autofill Project Info!"/>
        <Button onClick={async() => { await fillFieldsFromURL(); if(statusMessageType != "error") { await finalCheck(); }}} text="And Final Check!"/>
    </li>
    <!-- Base project info -->
    {#if !requiredOptions.checkAllAtOnce}
        <li>Group Number / Identifier: <InputField bind:inputState={requiredOptions.group}/></li>
        <div class="vertical-spacer"></div>
        <li>First Name: <InputField bind:inputState={autoFillableOptions.firstName}/></li>
        <li>Last Name: <InputField bind:inputState={autoFillableOptions.lastName}/></li>
        <li>Project Folder Name: <InputField bind:inputState={autoFillableOptions.projectFolderName}/></li>
        <li>Project has Corrected + Raw folders: <CheckField bind:enabledState={autoFillableOptions.hasCorrectedItems}/></li>
        <li>Custom Group Folder Name: <InputField bind:inputState={autoFillableOptions.customGroupFolderName}/></li>
    {/if}
    <!-- Group photo info -->
    {#if !requiredOptions.checkAllAtOnce && requiredOptions.mediaType == "Photo"}
        <div class="vertical-spacer"></div>
        <li>Photo type: <OptionsField bind:optionState={photoOptions.photoType} options={photoTypeOptions} unselectedText="Photo Type"/></li>
        <li>DPI options: <OptionsField bind:optionState={photoOptions.dpi} options={dpiOptions} unselectedText="DPI"/></li>
        <li>Normal scans count: <InputField bind:inputState={photoOptions.normalScansCount}/></li>
        <li>Handscans count: <InputField bind:inputState={photoOptions.handScansCount}/></li>
        <li>Oversized Handscans count: <InputField bind:inputState={photoOptions.oshScansCount}/></li>
    {/if}
    <div class="vertical-spacer"></div>
    <button onclick={finalCheck}> Final check! </button>

    {#if statusMessage}
        <div class="vertical-spacer"></div>
        <li>
            <span style="color: {statusMessageType == "error" ? "red" : statusMessageType == "success" ? "green" : "var(--clr-primary)"};">{statusMessage}</span>
        </li>
    {/if}
</ol>



<style>
    li {
        display: block;
        margin-top: var(--s4);
    }
    .vertical-spacer {
        margin-top: var(--s16);
    }
</style>