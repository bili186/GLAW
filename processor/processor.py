import logging
import os
import time
import torch
from utils.meter import AverageMeter
from utils.metrics import Evaluator
from utils.comm import get_rank, synchronize
from torch.utils.tensorboard import SummaryWriter
import torch.nn as nn
import torch.nn.functional as F


def do_train(start_epoch, args, model, train_loader, evaluator, optimizer, scheduler, checkpointer):
    log_period = args.log_period
    eval_period = args.eval_period
    device = "cuda"
    num_epoch = args.num_epoch
    arguments = {}
    arguments["num_epoch"] = num_epoch
    arguments["iteration"] = 0

    logger = logging.getLogger("GLAW.train")
    logger.info('start training')

    meters = {"loss": AverageMeter()}
    tb_writer = SummaryWriter(log_dir=args.output_dir)
    best_top1 = 0.0

    for epoch in range(start_epoch, num_epoch + 1):
        start_time = time.time()
        for meter in meters.values():
            meter.reset()

        model.train()
        for n_iter, batch in enumerate(train_loader):
            batch = {k: v.to(device) for k, v in batch.items()}

            ret = model(batch)
            total_loss = ret['loss']

            batch_size = batch['images'].shape[0]
            meters['loss'].update(total_loss.item(), batch_size)

            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
            synchronize()

            if (n_iter + 1) % log_period == 0:
                logger.info(f"Epoch[{epoch}] Iter[{n_iter+1}/{len(train_loader)}] loss: {meters['loss'].avg:.4f} Lr: {scheduler.get_lr()[0]:.2e}")

        tb_writer.add_scalar('lr', scheduler.get_lr()[0], epoch)
        tb_writer.add_scalar('loss', meters['loss'].avg, epoch)
        scheduler.step()

        end_time = time.time()
        time_per_batch = (end_time - start_time) / (n_iter + 1)
        logger.info(f"Epoch {epoch} done. {time_per_batch:.3f}s/batch Speed: {train_loader.batch_size/time_per_batch:.1f}samples/s")

        if epoch % eval_period == 0:
            logger.info(f"Validation Results - Epoch: {epoch}")
            if args.distributed:
                top1 = evaluator.eval(model.module.eval())
            else:
                top1 = evaluator.eval(model.eval())
            torch.cuda.empty_cache()
            if best_top1 < top1:
                best_top1 = top1
                arguments["epoch"] = epoch
                checkpointer.save("best", **arguments)

    logger.info(f"best R1: {best_top1} at epoch {arguments['epoch']}")
    arguments["epoch"] = epoch
    checkpointer.save("last", **arguments)


def do_inference(model, test_img_loader, test_txt_loader):
    logger = logging.getLogger("GLAW.test")
    logger.info("Enter inferencing")
    evaluator = Evaluator(test_img_loader, test_txt_loader)
    evaluator.eval(model.eval())