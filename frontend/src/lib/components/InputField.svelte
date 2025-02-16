<script lang="ts">
    interface Props {
        inputState : string
    };

    let { inputState: inputState = $bindable() } : Props = $props();
</script>



<input bind:value={inputState} placeholder={"Enter a value here..."}/>