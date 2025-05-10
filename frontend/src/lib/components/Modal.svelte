<script lang="ts">
    import { disableScrollHandling } from "$app/navigation";
    import type { Snippet } from "svelte";
    import Button from "./Button.svelte";

	let dialog: HTMLDialogElement;

    $effect(() => {
        if(showModal) {
            dialog.showModal();
        }
    });

    let {
        showModal = $bindable(),
        header,
        children
    } : {
		showModal: boolean,
        header: Snippet,
        children: Snippet
    } = $props();
</script>


<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
<dialog
    bind:this={dialog}
    onclose={() => (showModal = false)}
    onclick={(e) => {
        if (e.target === dialog) {
			dialog.close();
        }
    }}
    class="bordered"
>
    <div>
        {@render header?.()}
        <hr />
        {@render children?.()}
        <hr />
        <!-- svelte-ignore a11y_autofocus -->
        <Button onClick={() => dialog.close()}>
			Close
		</Button>	
    </div>
</dialog>


<style>
	dialog {
		max-width: 800px;
		border-radius: 0.2em;
		border: none;
		padding: 0;
        background-color: var(--clr-background);
        color: var(--clr-primary);
	}
	dialog::backdrop {
		background: rgba(0, 0, 0, 0.3);
	}
	dialog > div {
		padding: 1em;
	}
	dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}
	@keyframes zoom {
		from {
			transform: scale(0.95);
		}
		to {
			transform: scale(1);
		}
	}
	dialog[open]::backdrop {
		animation: fade 0.2s ease-out;
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>