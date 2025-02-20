export class StatusMessage {
    public message = "";
    public status = "";


    public constructor(message : string, status : string) {
        this.message = message;
        this.status = status;
    }


    public static empty() : StatusMessage {
        return new StatusMessage("", "");
    }

    public static errorMessage(error : string) : StatusMessage {
        return new StatusMessage(error, "error");
    }
    public static fieldNotSetErrorMessage(field : string) : StatusMessage {
        return StatusMessage.errorMessage(`Please enter a value for ${field}!`);
    }
    public getAddedErrorMessage(error : string) : StatusMessage {
        return StatusMessage.errorMessage(`${this.message ? `${this.message}, ` : ""}${error}`);
    }

    public static normalMessage(message : string) : StatusMessage {
        return new StatusMessage(message, "");
    }
    public static thinkingMessage() : StatusMessage {
        return StatusMessage.normalMessage("Thinking...");
    }

    public static successMessage(success : string) : StatusMessage {
        return new StatusMessage(success, "succcess");
    }
}