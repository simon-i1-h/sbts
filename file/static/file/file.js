let upload = document.querySelector('#upload');

upload.addEventListener('click', async ev => {
    let csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let file_elem = document.querySelector('#file');

    if (file_elem.files.length !== 1) {
        return;
    }

    let file = file_elem.files[0];

    try {
        let resp = await fetch('/api/blobs/', {
            method: 'POST',
            mode: 'same-origin',
            headers: {
                'Content-Type': 'application/octet-stream',
                'X-CSRFToken': csrf_token,
            },
            body: file,
        });

        if (!resp.ok) {
            throw new Error(await resp.text());
        }

        let {key} = await resp.json();

        resp = await fetch('/api/files/', {
            method: 'POST',
            mode: 'same-origin',
            headers: {
                'X-CSRFToken': csrf_token,
            },
            body: new URLSearchParams({
                key: key,
                name: file.name,
                size: file.size,
            }),
        });

        if (!resp.ok) {
            throw new Error(await resp.text());
        }

        window.location.reload();
    } catch (e) {
        console.error(e);
    }
});
