import { StatusMessage } from "$lib/scripts/statusMessage";

export function VerifyIsNumber(): string {
    return "";
}


function tryParseGooglesheetsUrl(url : string) : string {
    if(url.includes("/")) {
        const split = url.split("/");
        if(split.length != 7) {
            throw new Error("Please enter a valid Google Sheets URL or ID!");
        }
        url = split[5];
    }

    if(url == "") {
        throw new Error("Please enter a URL!");
    }
    
    return url;
}


export function parseGoogleSheetsUrlOrError(
url : string, setUrl : (input : string) => void,
setError : (input : StatusMessage) => void) : boolean {
    try {
        setUrl(tryParseGooglesheetsUrl(url));
        return true;
    } catch (e) {
        setError(StatusMessage.errorMessage((e as Error).message));
        return false;
    }
}