#!/usr/local/bin/node

import { spawnSync } from 'child_process'
import { createWriteStream, existsSync, mkdirSync } from 'fs'
import { get } from 'https'
import { join } from 'path'
import { parse as queryParser } from 'querystring'
import { parse as urlParser } from 'url'
import { debuglog } from 'util'

const log = debuglog('wallpaper')

// for additional debugging output:
//   NODE_DEBUG=wallpaper download-bing-wallpaper.mjs

const { HOME } = process.env

const BING_INDEX_URL = 'https://www.bing.com/'
const WALLPAPERS_DIR = `${HOME}/Google Drive/Pictures/Bing`
const DAYS_TO_RETAIN_WALLPAPERS = 365

log('retaining wallpapers for %d days', DAYS_TO_RETAIN_WALLPAPERS)

process.on('unhandledRejection', console.error)

log('creating directory "%s"', WALLPAPERS_DIR)
mkdirSync(WALLPAPERS_DIR, { recursive: true })

const getBingIndexPage = url => {
  return new Promise((resolve, reject) => {
    const request = get(url, response => {
      let data = ''

      if (response.statusCode !== 200) {
        reject(new Error(`GET request failed with a ${response.statusCode}`))
      }

      response.on('data', chunk => data += chunk)
      response.on('end', () => resolve(data))
    })

    request.on('error', (err) => reject(err))
  })
}

const downloadWallpaperFromUrl = async urlObj => {
  const filename = queryParser(urlObj.query).id
    .replace(/^OHR./, '')
    .replace(/_EN-US[0-9]+/, '')
  const pathToFile = join(WALLPAPERS_DIR, filename)

  if (!existsSync(pathToFile)) {
    log('saving wallpaper as "%s"', pathToFile)
    const file = createWriteStream(pathToFile)

    get(urlObj, response => {
      response.pipe(file)
    })
  } else {
    log('file already exists: "%s"', pathToFile)
  }

  return pathToFile
}

const setDesktopPicture = wallpaper => {
  const args = [
    '-e',
    `tell application "Finder" to set desktop picture to POSIX file "${wallpaper}"`,
  ]

  const options = {
    stdio: 'ignore',
  }

  log('attempting to set desktop picture to "%s"', wallpaper)
  spawnSync('/usr/bin/osascript', args, options)
}

const removeOldFiles = async () => {
  const args = [
    WALLPAPERS_DIR,
    '-name',
    '*.jpg',
    '-ctime',
    `+${DAYS_TO_RETAIN_WALLPAPERS}`,
    '-delete',
  ]

  const options = {
    stdio: 'inherit',
  }

  log('removing old wallpapers')
  spawnSync('find', args, options)
}

const extractWallpaperUrl = async url => {
  let data
  let regex

  try {
    data = await getBingIndexPage(url)
    regex = /url:['"](.+?.jpg)/i
    const path = regex.exec(data)[1]
    const downloadUrl = urlParser(path.replace(/^.*\//, url))

    return downloadUrl
  } catch (error) {
    console.log('DATA:')
    console.dir(data)
    console.log('REGEX:')
    console.dir(regex)
    console.log('DATA AFTER REGEX:')
    console.dir(regex?.exec(data))
    console.log('ERROR:')
    console.error(error)
  }
}

const wallpaperUrl = await extractWallpaperUrl(BING_INDEX_URL)
const wallpaper = await downloadWallpaperFromUrl(wallpaperUrl)
setDesktopPicture(wallpaper)
await removeOldFiles()
