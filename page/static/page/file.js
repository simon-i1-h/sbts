let upload = document.querySelector('#upload');
let const_map = JSON.parse(document.querySelector('#file-data').text);
let url_map = const_map['url_map'];

upload.addEventListener('click', async ev => {
    let csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let file_elem = document.querySelector('#file');

    if (file_elem.files.length !== 1) {
        return;
    }

    let file = file_elem.files[0];

    try {
        let resp = await fetch(url_map['file:upload'], {
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

        resp = await fetch(url_map['file:create'], {
            method: 'POST',
            mode: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
            },
            body: JSON.stringify({
                key: key,
                name: file.name,
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
